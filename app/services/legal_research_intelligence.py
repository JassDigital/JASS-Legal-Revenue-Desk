"""Issue-led research bundles with source-backed arguments and contrary material."""
from app.services.legal_source_verification import VERIFICATION_STATES

POSITIONS=["Supports","Contrary","Relevant","Distinguishes","Procedural"]
ARGUMENT_TYPES=["Proposed","Supporting","Response to contrary authority","Counter-argument","Relief sought","Research note"]
def search_research_sources(conn,query="",verification="All",jurisdiction="All",limit=250):
 sql="""SELECT s.source_record_id,s.source_title,s.source_type,s.publisher,s.jurisdiction,s.source_identifier,
 s.publication_date,s.effective_from,s.effective_to,s.officiality,s.legal_status,s.verification_status,
 s.verified_by,s.verified_date,s.verification_notes,s.source_url,s.hash_sha256,
 m.title AS material_title,sec.section_number,sec.heading AS section_heading,sec.verification_status AS section_verification,
 j.case_title AS judgment_title,j.citation AS judgment_citation,j.court_name,j.decision_date,\n COALESCE(sec.section_number,j.citation,s.source_identifier) AS linked_reference,
 (SELECT COUNT(*) FROM legal_citation_links c WHERE c.source_record_id=s.source_record_id) citation_count
 FROM legal_source_records s
 LEFT JOIN revenue_law_materials m ON m.material_id=s.material_id
 LEFT JOIN revenue_law_sections sec ON sec.section_id=s.section_id
 LEFT JOIN judgments j ON j.judgment_id=s.judgment_id
 WHERE 1=1"""
 args=[]
 if query.strip():
  like="%"+query.strip()+"%"
  sql+=" AND (s.source_title LIKE ? OR s.source_identifier LIKE ? OR s.publisher LIKE ? OR s.verification_notes LIKE ? OR m.title LIKE ? OR sec.section_number LIKE ? OR sec.heading LIKE ? OR sec.section_text LIKE ? OR j.case_title LIKE ? OR j.citation LIKE ? OR j.full_text LIKE ? OR j.subject_keywords LIKE ?)"
  args += [like]*12
 if verification!="All":sql+=" AND s.verification_status=?";args.append(verification)
 if jurisdiction!="All":sql+=" AND s.jurisdiction=?";args.append(jurisdiction)
 sql+=" ORDER BY CASE s.verification_status WHEN 'legally_reviewed' THEN 0 WHEN 'copy_compared' THEN 1 WHEN 'identity_checked' THEN 2 ELSE 3 END,s.source_title LIMIT ?";args.append(limit)
 return conn.execute(sql,args).fetchall()
def bundles(conn,case_id=None):
 sql="""SELECT b.*,c.case_title FROM legal_research_bundles b LEFT JOIN revenue_cases c USING(case_id)"""
 args=()
 if case_id is not None:sql+=" WHERE b.case_id=?";args=(case_id,)
 return conn.execute(sql+" ORDER BY b.updated_at DESC,b.bundle_id DESC",args).fetchall()
def create_bundle(conn,v):
 if not (v.get("title") or "").strip():raise ValueError("Research bundle title is required.")
 cur=conn.execute("INSERT INTO legal_research_bundles(case_id,title,research_question,scope_notes,status) VALUES(?,?,?,?,?)",(v.get("case_id") or None,v["title"].strip(),v.get("research_question",""),v.get("scope_notes",""),v.get("status","Working")))
 conn.commit();return cur.lastrowid
def update_bundle(conn,bid,v):
 if not (v.get("title") or "").strip():raise ValueError("Research bundle title is required.")
 conn.execute("UPDATE legal_research_bundles SET title=?,research_question=?,scope_notes=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE bundle_id=?",(v["title"].strip(),v.get("research_question",""),v.get("scope_notes",""),v.get("status","Working"),bid));conn.commit()
def delete_bundle(conn,bid):
 conn.execute("DELETE FROM legal_research_bundles WHERE bundle_id=?",(bid,));conn.commit()
def bundle_issues(conn,bid):
 return conn.execute("SELECT * FROM legal_research_issues WHERE bundle_id=? ORDER BY research_issue_id",(bid,)).fetchall()
def create_issue(conn,bid,v):
 if not (v.get("issue_title") or "").strip():raise ValueError("Issue title is required.")
 cur=conn.execute("INSERT INTO legal_research_issues(bundle_id,issue_title,material_facts,legal_question,provisional_view,issue_status) VALUES(?,?,?,?,?,?)",(bid,v["issue_title"].strip(),v.get("material_facts",""),v.get("legal_question",""),v.get("provisional_view",""),v.get("issue_status","Open")))
 conn.commit();return cur.lastrowid
def update_issue(conn,iid,v):
 if not (v.get("issue_title") or "").strip():raise ValueError("Issue title is required.")
 conn.execute("UPDATE legal_research_issues SET issue_title=?,material_facts=?,legal_question=?,provisional_view=?,issue_status=?,updated_at=CURRENT_TIMESTAMP WHERE research_issue_id=?",(v["issue_title"].strip(),v.get("material_facts",""),v.get("legal_question",""),v.get("provisional_view",""),v.get("issue_status","Open"),iid));conn.commit()
def delete_issue(conn,iid):
 conn.execute("DELETE FROM legal_research_issues WHERE research_issue_id=?",(iid,));conn.commit()
def arguments(conn,iid):
 return conn.execute("SELECT * FROM legal_research_arguments WHERE research_issue_id=? ORDER BY argument_id",(iid,)).fetchall()
def add_argument(conn,iid,v):
 if not (v.get("argument_text") or "").strip():raise ValueError("Argument text is required.")
 cur=conn.execute("INSERT INTO legal_research_arguments(research_issue_id,argument_type,argument_text,status,notes) VALUES(?,?,?,?,?)",(iid,v.get("argument_type","Proposed"),v["argument_text"].strip(),v.get("status","Draft"),v.get("notes","")))
 conn.commit();return cur.lastrowid
def delete_argument(conn,aid):
 conn.execute("DELETE FROM legal_research_arguments WHERE argument_id=?",(aid,));conn.commit()
def attach_source(conn,iid,sid,v):
 if not conn.execute("SELECT 1 FROM legal_source_records WHERE source_record_id=?",(sid,)).fetchone():raise ValueError("Source record not found.")
 conn.execute("""INSERT OR IGNORE INTO legal_research_issue_sources(research_issue_id,source_record_id,position,pinpoint,relevance_note,proposition,verification_status)
 VALUES(?,?,?,?,?,?,?)""",(iid,sid,v.get("position","Relevant"),v.get("pinpoint",""),v.get("relevance_note",""),v.get("proposition",""),v.get("verification_status","unverified")))
 conn.commit()
def issue_sources(conn,iid):
 return conn.execute("""SELECT x.*,s.source_title,s.source_type,s.publisher,s.officiality,s.legal_status,s.verification_status AS source_verification,s.verified_by,s.verified_date,s.source_url,s.source_identifier,s.hash_sha256,m.title AS material_title,sec.section_number,j.case_title AS judgment_title,j.citation AS judgment_citation,j.court_name,j.decision_date
 FROM legal_research_issue_sources x JOIN legal_source_records s USING(source_record_id)
 LEFT JOIN revenue_law_materials m ON m.material_id=s.material_id LEFT JOIN revenue_law_sections sec ON sec.section_id=s.section_id LEFT JOIN judgments j ON j.judgment_id=s.judgment_id
 WHERE x.research_issue_id=? ORDER BY CASE x.position WHEN 'Supports' THEN 0 WHEN 'Contrary' THEN 1 ELSE 2 END,x.issue_source_id""",(iid,)).fetchall()
def detach_source(conn,xid):
 conn.execute("DELETE FROM legal_research_issue_sources WHERE issue_source_id=?",(xid,));conn.commit()
def build_bundle_report(conn,bid):
 b=conn.execute("SELECT b.*,c.case_title FROM legal_research_bundles b LEFT JOIN revenue_cases c USING(case_id) WHERE b.bundle_id=?",(bid,)).fetchone()
 if not b:raise ValueError("Research bundle not found.")
 out=["JASS LEGAL & REVENUE DESK — LEGAL RESEARCH BUNDLE","="*70,"",f"Bundle: {b['title']}",f"Case: {b['case_title'] or 'General research'}",f"Status: {b['status']}",f"Research question: {b['research_question']}",f"Scope: {b['scope_notes']}"]
 for issue in bundle_issues(conn,bid):
  out += ["","-"*70,f"ISSUE {issue['research_issue_id']}: {issue['issue_title']}",f"Material facts: {issue['material_facts']}",f"Legal question: {issue['legal_question']}",f"Provisional view (not a conclusion): {issue['provisional_view']}","ARGUMENTS"]
  for a in arguments(conn,issue["research_issue_id"]):out.append(f"- {a['argument_type']} [{a['status']}]: {a['argument_text']}\n  Notes: {a['notes']}")
  out.append("SOURCES — SUPPORTING, CONTRARY AND OTHER")
  for x in issue_sources(conn,issue["research_issue_id"]):
   out += [f"- {x['position']}: {x['source_title']}",f"  Type/publisher: {x['source_type']} / {x['publisher']}",f"  Identifier: {x['source_identifier']}",f"  Pinpoint: {x['pinpoint']}",f"  Proposition: {x['proposition']}",f"  Relevance: {x['relevance_note']}",f"  Source verification: {x['source_verification']} (issue link: {x['verification_status']})",f"  Legal status: {x['legal_status']}; officiality: {x['officiality']}",f"  Reviewer: {x['verified_by']} / {x['verified_date']}",f"  URL: {x['source_url']}",f"  SHA-256: {x['hash_sha256']}"]
 out += ["","RESEARCH SAFEGUARDS","- Search results are limited to source records entered in the local Legal Source Verification register; absence from results does not mean no authority exists.",
 "- Supporting and contrary labels are researcher classifications, not judicial determinations. Search for adverse authority and later treatment independently.",
 "- A source's officiality, verification and legal-status fields are human-entered. An official host or SHA-256 hash does not establish authenticity, commencement, current force, territorial application or precedential status.",
 "- Check exact text, pinpoint, effective date, amendments, repeal/savings provisions, court hierarchy, later treatment and procedural posture before relying on a proposition.",
 "- This bundle organizes research and draft arguments; it does not provide legal advice or determine the outcome."]
 return "\n".join(out)
