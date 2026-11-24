"""Case procedure workflow tracker. Templates are planning prompts, not statements of law."""
PROCEEDING_TYPES=["Mutation proceedings","Partition proceedings","Appeal","Revision","Correction of revenue record","Abadi Deh matter","Other"]
STATUSES=["Working","For review","Pending before authority","Disposed","Closed","On hold"]
STAGES=["Initial assessment","Record collection","Legal research","Draft preparation","Filing preparation","Filed","Notice / service","Hearing","Order awaited","Post-order action","Completed"]
STEP_STATUSES=["Not started","In progress","Waiting","Completed","Not applicable"]
VERIFICATION=["unverified","source_checked","copy_compared","disputed"]
# These are deliberately generic preparation prompts; no procedural step or deadline is represented as mandatory.
TEMPLATES={
 "Mutation proceedings":[
  "Obtain the complete mutation entry and supporting papers",
  "Obtain relevant Jamabandi and record-of-rights extracts",
  "Identify affected parties and service/notice record",
  "Record objections, statements and evidence available",
  "Locate applicable statutory provisions and current rules",
  "Record orders, dates and next procedural action"],
 "Partition proceedings":[
  "Obtain current Jamabandi and co-sharer particulars",
  "Verify estate, holding, Khewat, Khata and Khasra details",
  "Identify co-sharers and recorded shares; note disputed shares",
  "Collect map, field book and relevant revenue records if available",
  "Research applicable partition provisions and rules",
  "Record mode-of-partition issues, objections and orders"],
 "Appeal":[
  "Obtain certified copy of the order under challenge",
  "Record date of order and date copy became available",
  "Identify appellate forum and jurisdiction from current source",
  "Research limitation provision, applicable rules and exclusions",
  "Record limitation opinion, source and reviewer",
  "Prepare grounds, annexures and filing checklist"],
 "Revision":[
  "Obtain order and complete record of proceedings",
  "Identify revisional authority and statutory source",
  "Research scope, maintainability and limitation from current law",
  "Record procedural history and jurisdictional issues",
  "Prepare grounds and supporting documents"],
 "Correction of revenue record":[
  "Obtain the entry sought to be corrected and its source record",
  "Identify nature of alleged error and affected persons",
  "Research appropriate statutory route and competent authority",
  "Collect supporting primary documents and prior orders",
  "Record objections, notice and outcome"]
}
def list_proceedings(conn,case_id=None):
 sql="""SELECT p.*,c.case_title FROM revenue_proceeding_plans p JOIN revenue_cases c USING(case_id)"""
 args=()
 if case_id is not None:sql+=" WHERE p.case_id=?";args=(case_id,)
 sql+=" ORDER BY p.updated_at DESC,p.proceeding_id DESC"
 return conn.execute(sql,args).fetchall()
def create_proceeding(conn,v):
 if not v.get("case_id"):raise ValueError("Select a case.")
 if not v.get("proceeding_type"):raise ValueError("Proceeding type is required.")
 cur=conn.execute("""INSERT INTO revenue_proceeding_plans(case_id,proceeding_type,forum_name,case_reference,start_date,
 current_stage,status,limitation_start_date,limitation_period_note,limitation_source_reference,
 limitation_reviewed_by,limitation_reviewed_date,limitation_due_date,limitation_caveat,strategy_notes)
 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(v.get("case_id"),v.get("proceeding_type"),v.get("forum_name") or None,
 v.get("case_reference") or None,v.get("start_date") or None,v.get("current_stage","Preparation"),v.get("status","Working"),
 v.get("limitation_start_date") or None,v.get("limitation_period_note",""),v.get("limitation_source_reference",""),
 v.get("limitation_reviewed_by") or None,v.get("limitation_reviewed_date") or None,v.get("limitation_due_date") or None,
 v.get("limitation_caveat",""),v.get("strategy_notes","")))
 conn.commit();return cur.lastrowid
def get_proceeding(conn,pid):
 return conn.execute("SELECT p.*,c.case_title FROM revenue_proceeding_plans p JOIN revenue_cases c USING(case_id) WHERE p.proceeding_id=?",(pid,)).fetchone()
def update_proceeding(conn,pid,v):
 conn.execute("""UPDATE revenue_proceeding_plans SET proceeding_type=?,forum_name=?,case_reference=?,start_date=?,
 current_stage=?,status=?,limitation_start_date=?,limitation_period_note=?,limitation_source_reference=?,
 limitation_reviewed_by=?,limitation_reviewed_date=?,limitation_due_date=?,limitation_caveat=?,strategy_notes=?,
 updated_at=CURRENT_TIMESTAMP WHERE proceeding_id=?""",(v.get("proceeding_type"),v.get("forum_name") or None,
 v.get("case_reference") or None,v.get("start_date") or None,v.get("current_stage","Preparation"),v.get("status","Working"),
 v.get("limitation_start_date") or None,v.get("limitation_period_note",""),v.get("limitation_source_reference",""),
 v.get("limitation_reviewed_by") or None,v.get("limitation_reviewed_date") or None,v.get("limitation_due_date") or None,
 v.get("limitation_caveat",""),v.get("strategy_notes",""),pid))
 conn.commit()
def delete_proceeding(conn,pid):
 conn.execute("DELETE FROM revenue_proceeding_plans WHERE proceeding_id=?",(pid,));conn.commit()
def steps(conn,pid):
 return conn.execute("SELECT * FROM revenue_proceeding_steps WHERE proceeding_id=? ORDER BY step_order,step_id",(pid,)).fetchall()
def add_step(conn,pid,v):
 if not v.get("step_title","").strip():raise ValueError("Step title is required.")
 cur=conn.execute("""INSERT INTO revenue_proceeding_steps(proceeding_id,step_order,step_title,description,step_status,
 target_date,completed_date,responsible_person,source_reference,verification_status,notes)
 VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(pid,v.get("step_order",0),v["step_title"].strip(),v.get("description",""),v.get("step_status","Not started"),v.get("target_date") or None,v.get("completed_date") or None,v.get("responsible_person",""),v.get("source_reference",""),v.get("verification_status","unverified"),v.get("notes","")))
 conn.commit();return cur.lastrowid
def update_step(conn,sid,v):
 conn.execute("""UPDATE revenue_proceeding_steps SET step_order=?,step_title=?,description=?,step_status=?,target_date=?,
 completed_date=?,responsible_person=?,source_reference=?,verification_status=?,notes=?,updated_at=CURRENT_TIMESTAMP
 WHERE step_id=?""",(v.get("step_order",0),v["step_title"].strip(),v.get("description",""),v.get("step_status","Not started"),v.get("target_date") or None,v.get("completed_date") or None,v.get("responsible_person",""),v.get("source_reference",""),v.get("verification_status","unverified"),v.get("notes",""),sid));conn.commit()
def delete_step(conn,sid):
 conn.execute("DELETE FROM revenue_proceeding_steps WHERE step_id=?",(sid,));conn.commit()
def events(conn,pid):
 return conn.execute("SELECT * FROM revenue_proceeding_events WHERE proceeding_id=? ORDER BY COALESCE(event_date,''),event_id",(pid,)).fetchall()
def add_event(conn,pid,v):
 if not v.get("title","").strip():raise ValueError("Event title is required.")
 conn.execute("""INSERT INTO revenue_proceeding_events(proceeding_id,event_date,event_type,title,details,next_action,
 deadline_date,source_reference,status) VALUES(?,?,?,?,?,?,?,?,?)""",(pid,v.get("event_date") or None,v.get("event_type","Other"),v["title"].strip(),v.get("details",""),v.get("next_action",""),v.get("deadline_date") or None,v.get("source_reference",""),v.get("status","Open")));conn.commit()
def delete_event(conn,eid):
 conn.execute("DELETE FROM revenue_proceeding_events WHERE event_id=?",(eid,));conn.commit()
def apply_template(conn,pid,proceeding_type):
 titles=TEMPLATES.get(proceeding_type,[])
 existing={r["step_title"].casefold() for r in steps(conn,pid)}
 added=0
 for i,title in enumerate(titles,1):
  if title.casefold() not in existing:
   add_step(conn,pid,{"step_order":i*10,"step_title":title,"description":"Planning prompt only. Confirm whether this is applicable and cite the current legal/procedural source before treating it as a requirement.","step_status":"Not started","verification_status":"unverified"})
   added+=1
 return added
def build_proceeding_report(conn,pid):
 p=get_proceeding(conn,pid)
 if not p:raise ValueError("Proceeding not found.")
 out=["JASS LEGAL & REVENUE DESK — PROCEDURE WORKING SHEET","="*65,"",
 f"Case: {p['case_title']}",f"Proceeding: {p['proceeding_type']}",f"Forum: {p['forum_name'] or 'Not recorded'}",
 f"Case reference: {p['case_reference'] or 'Not recorded'}",f"Start date: {p['start_date'] or 'Not recorded'}",
 f"Stage: {p['current_stage']}",f"Status: {p['status']}","","LIMITATION REVIEW — USER ENTERED, NOT CALCULATED",
 f"Starting event/date: {p['limitation_start_date'] or 'Not recorded'}",
 f"Period / legal note: {p['limitation_period_note'] or 'Not recorded'}",
 f"Source reference: {p['limitation_source_reference'] or 'Not recorded'}",
 f"Reviewed by/date: {p['limitation_reviewed_by'] or 'Not recorded'} / {p['limitation_reviewed_date'] or 'Not recorded'}",
 f"User-entered proposed due date: {p['limitation_due_date'] or 'Not recorded'}",
 f"Caveats: {p['limitation_caveat'] or 'Not recorded'}","","PROCEDURAL CHECKLIST"]
 for r in steps(conn,pid):
  out.append(f"- [{r['step_status']}] {r['step_title']} — target {r['target_date'] or 'not set'}; completed {r['completed_date'] or 'not recorded'}")
  if r["description"]:out.append("  "+r["description"])
  out.append(f"  Source: {r['source_reference'] or 'Not recorded'}; verification: {r['verification_status']}; notes: {r['notes']}")
 out += ["","PROCEEDING CHRONOLOGY / DEADLINES"]
 for r in events(conn,pid):out.append(f"- {r['event_date'] or 'Undated'} | {r['event_type']} | {r['title']} | deadline: {r['deadline_date'] or 'not recorded'} | status: {r['status']}\n  {r['details']}\n  Next action: {r['next_action']}\n  Source: {r['source_reference']}")
 out += ["","STRATEGY NOTES",p["strategy_notes"] or "None recorded",
 "","IMPORTANT: This tracker does not calculate limitation, determine maintainability, identify the correct forum, or establish mandatory procedure. Verify the current statute, amendments, rules, applicable notifications, certified orders, copy-delivery dates, exclusions, condonation provisions and local filing practice with a qualified professional or competent authority. Generic checklist prompts are not legal advice."]
 return "\n".join(out)
