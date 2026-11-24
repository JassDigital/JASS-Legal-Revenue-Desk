"""Research-to-draft assembly. Generates a structured working scaffold, not legal advice."""
from app.services.revenue_drafting_service import save_draft

def eligible_bundles(conn,case_id):
 return conn.execute("""SELECT * FROM legal_research_bundles WHERE case_id=? OR case_id IS NULL
 ORDER BY updated_at DESC,bundle_id DESC""",(case_id,)).fetchall()

def draft_package(conn,bundle_id):
 bundle=conn.execute("SELECT * FROM legal_research_bundles WHERE bundle_id=?",(bundle_id,)).fetchone()
 if not bundle:raise ValueError("Research bundle not found.")
 issues=conn.execute("SELECT * FROM legal_research_issues WHERE bundle_id=? ORDER BY research_issue_id",(bundle_id,)).fetchall()
 sources=[];out=["WORKING DRAFT — RESEARCH-BASED SCAFFOLD","="*68,"",f"Research bundle: {bundle['title']}",f"Research question: {bundle['research_question']}",f"Scope: {bundle['scope_notes']}","",
 "DRAFTING NOTE: This is a structured working scaffold assembled from the selected research bundle. It is not a prescribed court form, legal opinion, verified statement of fact or filing-ready document. Complete and verify all bracketed particulars, procedural requirements, relief and citations."]
 for n,issue in enumerate(issues,1):
  out += ["","-"*68,f"ISSUE {n}: {issue['issue_title']}","MATERIAL FACTS (verify against the record)",issue["material_facts"] or "[Insert and verify material facts.]","LEGAL QUESTION",issue["legal_question"] or "[State the precise legal question.]","PROPOSED SUBMISSIONS — RESEARCH NOTES"]
  args=conn.execute("SELECT * FROM legal_research_arguments WHERE research_issue_id=? ORDER BY argument_id",(issue["research_issue_id"],)).fetchall()
  if args:
   for a in args:out.append(f"[{a['argument_type']} — {a['status']}]\n{a['argument_text']}\nResearch notes / gaps: {a['notes']}")
  else:out.append("[Develop the submission after reviewing supporting and contrary authorities.]")
  out += ["PROVISIONAL VIEW (not a legal conclusion)",issue["provisional_view"] or "[Record uncertainties and alternative views.]","SOURCE REFERENCES"]
  linked=conn.execute("""SELECT x.*,s.source_title,s.source_type,s.source_identifier,s.source_url,s.verification_status AS source_verification,s.legal_status,s.officiality
   FROM legal_research_issue_sources x JOIN legal_source_records s USING(source_record_id)
   WHERE x.research_issue_id=? ORDER BY CASE x.position WHEN 'Supports' THEN 0 WHEN 'Contrary' THEN 1 ELSE 2 END,x.issue_source_id""",(issue["research_issue_id"],)).fetchall()
  if linked:
   for x in linked:
    out.append(f"[{x['position']}] {x['source_title']} — {x['pinpoint'] or '[pinpoint to verify]'}\nProposition: {x['proposition']}\nSource verification: {x['source_verification']}; legal status: {x['legal_status']}; officiality: {x['officiality']}\nURL: {x['source_url']}")
    sources.append(x)
  else:out.append("[No source linked to this issue. Research and record relevant primary authorities.]")
 out += ["","RELIEF / PRAYER (complete and verify independently)","[Set out precise relief supported by the facts, jurisdiction and applicable law.]","","VERIFICATION / ANNEXURES","[Complete the applicable verification, affidavit, annexure index, service and filing requirements after checking the governing rules.]","","RESEARCH SAFEGUARDS","- Include adverse authority and explain any distinction; do not omit contrary material.","- Confirm current statutory text, commencement, territorial application, amendments, repeal/savings and effective date.","- Confirm judgment citation, court hierarchy, later treatment, pinpoint paragraph and procedural posture.","- Confirm forum, jurisdiction, limitation, prescribed form, fees, service and filing method from current authoritative sources."]
 # De-duplicate exact repeated source link rows in the appendix.
 seen=set();unique=[]
 for x in sources:
  key=(x["source_record_id"],x["pinpoint"],x["position"])
  if key not in seen:seen.add(key);unique.append(x)
 return "\n".join(out),unique,bundle

def create_draft_from_bundle(conn,case_id,bundle_id,draft_type,title,status="Working"):
 body,sources,bundle=draft_package(conn,bundle_id)
 if bundle["case_id"] not in (None,case_id):raise ValueError("The selected research bundle belongs to a different case.")
 if not (title or "").strip():raise ValueError("Draft title is required.")
 draft_id=save_draft(conn,case_id,{"draft_type":draft_type,"title":title.strip(),"body":body,"status":status})
 conn.execute("UPDATE revenue_case_drafts SET research_bundle_id=? WHERE draft_id=?",(bundle_id,draft_id))
 for x in sources:
  conn.execute("""INSERT OR IGNORE INTO revenue_case_draft_sources(draft_id,source_record_id,source_title_snapshot,source_type_snapshot,source_identifier_snapshot,source_url_snapshot,position,pinpoint,proposition,verification_status,legal_status_snapshot,officiality_snapshot)
   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(draft_id,x["source_record_id"],x["source_title"],x["source_type"],x["source_identifier"],x["source_url"],x["position"],x["pinpoint"],x["proposition"],x["verification_status"],x["legal_status"],x["officiality"]))
 conn.commit();return draft_id

def draft_source_register(conn,draft_id):
 return conn.execute("SELECT * FROM revenue_case_draft_sources WHERE draft_id=? ORDER BY CASE position WHEN 'Supports' THEN 0 WHEN 'Contrary' THEN 1 ELSE 2 END,draft_source_id",(draft_id,)).fetchall()

def append_citation_schedule(conn,draft_id):
 rows=draft_source_register(conn,draft_id)
 out=["","SOURCE & PINPOINT SCHEDULE","="*60]
 if not rows:out.append("[No source links recorded for this draft.]")
 for i,r in enumerate(rows,1):
  out += [f"[{i}] [{r['position']}] {r['source_title_snapshot']}",f"    Type / identifier: {r['source_type_snapshot']} / {r['source_identifier_snapshot']}",f"    Pinpoint: {r['pinpoint'] or '[verify pinpoint]'}",f"    Proposition: {r['proposition']}",f"    Verification: {r['verification_status']}; legal status: {r['legal_status_snapshot']}; officiality: {r['officiality_snapshot']}",f"    Source URL: {r['source_url_snapshot']}"]
 return "\n".join(out)

def build_draft_export(conn,draft_id):
 r=conn.execute("SELECT d.*,b.title AS bundle_title FROM revenue_case_drafts d LEFT JOIN legal_research_bundles b ON b.bundle_id=d.research_bundle_id WHERE d.draft_id=?",(draft_id,)).fetchone()
 if not r:raise ValueError("Draft not found.")
 return "\n".join(["JASS LEGAL & REVENUE DESK — DRAFT EXPORT","="*68,"",f"Title: {r['title']}",f"Type: {r['draft_type']}",f"Status: {r['status']}",f"Version: {r['version']}",f"Research bundle: {r['bundle_title'] or 'Not linked'}","",r["body"],append_citation_schedule(conn,draft_id),"","NOTICE: Working draft only. Verify facts, legal propositions, citations, current law, forum, limitation, procedural rules, prescribed forms, service and filing requirements before use."])
