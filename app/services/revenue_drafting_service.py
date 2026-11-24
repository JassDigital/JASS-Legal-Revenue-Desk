"""Case drafting, evidence relationships and report assembly."""
DRAFT_TYPES=["Application","Appeal","Revision","Objections","Reply / Written statement","Written submissions","Evidence list","Other"]
DRAFT_STATUSES=["Working","For review","Finalised","Filed"]
def list_drafts(conn,case_id):
    return conn.execute("SELECT * FROM revenue_case_drafts WHERE case_id=? ORDER BY updated_at DESC,draft_id DESC",(case_id,)).fetchall()
def get_draft(conn,draft_id):
    return conn.execute("SELECT * FROM revenue_case_drafts WHERE draft_id=?",(draft_id,)).fetchone()
def save_draft(conn,case_id,values,draft_id=None):
    title=values.get("title","").strip()
    if not title:raise ValueError("Draft title is required.")
    if draft_id:
        conn.execute("""UPDATE revenue_case_drafts SET draft_type=?,title=?,body=?,status=?,version=version+1,
            updated_at=CURRENT_TIMESTAMP WHERE draft_id=? AND case_id=?""",
            (values["draft_type"],title,values["body"],values["status"],draft_id,case_id))
        result=draft_id
    else:
        cur=conn.execute("""INSERT INTO revenue_case_drafts(case_id,draft_type,title,body,status)
            VALUES(?,?,?,?,?)""",(case_id,values["draft_type"],title,values["body"],values["status"]))
        result=cur.lastrowid
    conn.commit();return result
def delete_draft(conn,draft_id):
    conn.execute("DELETE FROM revenue_case_drafts WHERE draft_id=?",(draft_id,));conn.commit()
def evidence_link_options(conn,case_id):
    ev=conn.execute("SELECT evidence_id,evidence_title FROM revenue_case_evidence WHERE case_id=? ORDER BY evidence_title",(case_id,)).fetchall()
    parties=conn.execute("SELECT party_id,party_name,role FROM revenue_case_parties WHERE case_id=? ORDER BY party_name",(case_id,)).fetchall()
    issues=conn.execute("SELECT issue_id,issue_title FROM revenue_case_issues WHERE case_id=? ORDER BY issue_title",(case_id,)).fetchall()
    return ev,parties,issues
def add_evidence_link(conn,evidence_id,party_id,issue_id,note=""):
    if party_id is None and issue_id is None:raise ValueError("Select a party or legal issue.")
    conn.execute("""INSERT OR IGNORE INTO revenue_case_evidence_links(evidence_id,party_id,issue_id,link_note)
        VALUES(?,?,?,?)""",(evidence_id,party_id,issue_id,note));conn.commit()
def list_evidence_links(conn,case_id):
    return conn.execute("""SELECT l.link_id,e.evidence_title,p.party_name,i.issue_title,l.link_note
        FROM revenue_case_evidence_links l JOIN revenue_case_evidence e USING(evidence_id)
        LEFT JOIN revenue_case_parties p USING(party_id) LEFT JOIN revenue_case_issues i USING(issue_id)
        WHERE e.case_id=? ORDER BY l.link_id DESC""",(case_id,)).fetchall()
def delete_evidence_link(conn,link_id):
    conn.execute("DELETE FROM revenue_case_evidence_links WHERE link_id=?",(link_id,));conn.commit()
def build_case_report(conn,case_id):
    c=conn.execute("SELECT * FROM revenue_cases WHERE case_id=?",(case_id,)).fetchone()
    if not c:raise ValueError("Case not found.")
    out=["JASS LEGAL & REVENUE DESK — CASE PREPARATION REPORT","="*64,"",f"Case: {c['case_title']}",f"Type: {c['case_type']}",f"Case number: {c['case_number'] or 'Not recorded'}",f"Authority: {c['authority'] or 'Not recorded'}",f"Status: {c['status']}",f"Priority: {c['priority']}",f"District / Tehsil / Village: {c['district'] or ''} / {c['tehsil'] or ''} / {c['village'] or ''}",f"Filing date: {c['filing_date'] or 'Not recorded'}",f"Next hearing: {c['next_hearing_date'] or 'Not recorded'}","", "CASE SUMMARY / RELIEF SOUGHT",c['case_summary'] or "Not recorded","","PARTIES"]
    for r in conn.execute("SELECT * FROM revenue_case_parties WHERE case_id=? ORDER BY party_id",(case_id,)):
        out.append(f"- {r['party_name']} — {r['role']}; representative: {r['representative'] or 'Not recorded'}; details: {r['address'] or ''}")
    out += ["","LAND / PROPERTY"]
    for r in conn.execute("SELECT * FROM revenue_case_properties WHERE case_id=? ORDER BY property_id",(case_id,)):
        out.append(f"- {r['village']}, {r['tehsil']}, {r['district']}; Hadbast {r['hadbast_number']}; Jamabandi {r['jamabandi_year']}; Khata {r['khata_number']}; Khatauni {r['khatauni_number']}; Khasra {r['khasra_numbers']}; Area {r['area']}; Share {r['ownership_share']}")
        if r['land_description']:out.append("  Description: "+r['land_description'])
    out += ["","CHRONOLOGY / HEARINGS"]
    for r in conn.execute("SELECT * FROM revenue_case_events WHERE case_id=? ORDER BY event_date,event_id",(case_id,)):
        out.append(f"- {r['event_date'] or 'Undated'} | {r['event_type']} | {r['title']}\n  {r['details']}\n  Next action: {r['next_action'] or 'None recorded'}")
    out += ["","EVIDENCE REGISTER"]
    for r in conn.execute("""SELECT e.*,d.document_title FROM revenue_case_evidence e LEFT JOIN documents d USING(document_id)
        WHERE e.case_id=? ORDER BY e.evidence_id""",(case_id,)):
        out.append(f"- {r['evidence_title']} ({r['evidence_type']}); library document: {r['document_title'] or 'Not linked'}; reference: {r['document_reference'] or ''}; verification: {r['verification_status']}; relevance: {r['relevance_notes']}")
    out += ["","EVIDENCE CONNECTIONS"]
    for r in list_evidence_links(conn,case_id):
        out.append(f"- {r['evidence_title']} → party: {r['party_name'] or '—'}; issue: {r['issue_title'] or '—'}; {r['link_note']}")
    out += ["","ISSUES & ARGUMENTS"]
    for r in conn.execute("SELECT * FROM revenue_case_issues WHERE case_id=? ORDER BY issue_id",(case_id,)):
        out.append(f"- {r['issue_title']} [{r['status']}]\n  Facts: {r['facts']}\n  Legal question: {r['legal_question']}\n  Proposed argument: {r['proposed_argument']}\n  Relevant law: {r['relevant_law']}")
    out += ["","DRAFT REGISTER"]
    for r in list_drafts(conn,case_id):out.append(f"- {r['draft_type']}: {r['title']} — {r['status']} (version {r['version']})")
    out += ["","PRIVATE PREPARATION NOTES",c['strategy_notes'] or "None recorded","","IMPORTANT: This is a user-prepared working report, not legal advice or a verified court filing. Check every fact, source, provision, deadline, format and procedural requirement with authoritative records and applicable rules."]
    return "\n".join(out)
