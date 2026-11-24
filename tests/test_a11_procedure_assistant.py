import sqlite3
import unittest
from app.database.migrations import migrate,CURRENT_SCHEMA_VERSION
from app.services.revenue_case_service import create_case
from app.services.revenue_procedure_service import (create_proceeding,get_proceeding,update_proceeding,delete_proceeding,
 steps,add_step,update_step,delete_step,events,add_event,delete_event,apply_template,build_proceeding_report,TEMPLATES)

class A11ProcedureTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row
  self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
  self.cid=create_case(self.conn,{"case_title":"Mutation case","case_type":"Mutation","status":"Preparing","priority":"Normal","district":"Sirsa","tehsil":"Dabwali","village":"Village X"})
  self.pid=create_proceeding(self.conn,{"case_id":self.cid,"proceeding_type":"Mutation proceedings","forum_name":"Revenue Officer","case_reference":"M-12","start_date":"2026-11-01","current_stage":"Record collection","status":"Working","limitation_start_date":"Order date, if applicable","limitation_period_note":"Manual research pending","limitation_source_reference":"Check current Act and rules","limitation_reviewed_by":"Not yet reviewed","limitation_reviewed_date":"","limitation_due_date":"","limitation_caveat":"Do not calculate until source checked","strategy_notes":"Collect certified copy"})
 def tearDown(self):self.conn.close()
 def test_schema_v11(self):
  self.assertGreaterEqual(CURRENT_SCHEMA_VERSION,11)
  self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],11)
  names={r["name"] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  self.assertTrue({"revenue_proceeding_plans","revenue_proceeding_steps","revenue_proceeding_events"}.issubset(names))
 def test_proceeding_create_update_delete(self):
  p=get_proceeding(self.conn,self.pid);self.assertEqual(p["case_id"],self.cid)
  update_proceeding(self.conn,self.pid,{"proceeding_type":"Appeal","forum_name":"Appellate authority","case_reference":"A-3","start_date":"2026-11-02","current_stage":"Draft preparation","status":"For review","limitation_start_date":"Copy date","limitation_period_note":"Review applicable provision","limitation_source_reference":"Act section and rules","limitation_reviewed_by":"Counsel","limitation_reviewed_date":"2026-11-03","limitation_due_date":"2026-11-20","limitation_caveat":"Subject to exclusions","strategy_notes":"Draft grounds"})
  self.assertEqual(get_proceeding(self.conn,self.pid)["proceeding_type"],"Appeal")
  delete_proceeding(self.conn,self.pid);self.assertIsNone(get_proceeding(self.conn,self.pid))
 def test_step_lifecycle(self):
  sid=add_step(self.conn,self.pid,{"step_order":10,"step_title":"Obtain certified record","description":"Check copy","step_status":"Not started","target_date":"2026-11-30","source_reference":"Revenue record","verification_status":"source_checked","notes":""})
  self.assertEqual(steps(self.conn,self.pid)[0]["step_title"],"Obtain certified record")
  update_step(self.conn,sid,{"step_order":10,"step_title":"Obtain certified record","description":"Updated","step_status":"Completed","target_date":"2026-11-30","completed_date":"2026-11-20","source_reference":"Order page 4","verification_status":"copy_compared","notes":"Done"})
  self.assertEqual(steps(self.conn,self.pid)[0]["step_status"],"Completed")
  delete_step(self.conn,sid);self.assertEqual(len(steps(self.conn,self.pid)),0)
 def test_event_deadline_lifecycle(self):
  add_event(self.conn,self.pid,{"event_date":"2026-11-20","event_type":"Hearing","title":"First hearing","details":"Notice","next_action":"Prepare reply","deadline_date":"2026-11-25","source_reference":"Order dated 20 Nov","status":"Open"})
  self.assertEqual(events(self.conn,self.pid)[0]["deadline_date"],"2026-11-25")
  eid=events(self.conn,self.pid)[0]["event_id"];delete_event(self.conn,eid);self.assertEqual(len(events(self.conn,self.pid)),0)
 def test_templates_are_generic_and_idempotent(self):
  count=apply_template(self.conn,self.pid,"Mutation proceedings")
  self.assertEqual(count,len(TEMPLATES["Mutation proceedings"]))
  self.assertEqual(apply_template(self.conn,self.pid,"Mutation proceedings"),0)
  self.assertTrue(all("Planning prompt only" in r["description"] for r in steps(self.conn,self.pid)))
 def test_report_carries_limitation_warning(self):
  add_event(self.conn,self.pid,{"event_date":"","event_type":"Deadline","title":"User-entered date","deadline_date":"2026-12-01","status":"Open"})
  report=build_proceeding_report(self.conn,self.pid)
  for phrase in ["LIMITATION REVIEW","User-entered proposed due date","PROCEDURAL CHECKLIST","PROCEEDING CHRONOLOGY","does not calculate limitation","not legal advice"]:
   self.assertIn(phrase,report)
 def test_case_delete_cascades_proceeding(self):
  delete_proceeding(self.conn,self.pid)
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM revenue_proceeding_plans").fetchone()[0],0)
  # A separate proceeding is removed when its parent case is deleted.
  pid=create_proceeding(self.conn,{"case_id":self.cid,"proceeding_type":"Other","current_stage":"Preparation","status":"Working"})
  self.conn.execute("DELETE FROM revenue_cases WHERE case_id=?",(self.cid,));self.conn.commit()
  self.assertIsNone(get_proceeding(self.conn,pid))

if __name__=="__main__":unittest.main()
