import sqlite3,unittest
from datetime import date,timedelta
from app.database.migrations import migrate,CURRENT_SCHEMA_VERSION
from app.services.revenue_case_service import create_case
from app.services.revenue_case_intelligence import (case_dashboard_rows,upcoming_hearings,recorded_deadlines,
 outstanding_steps,manually_recorded_limitation_reviews,dashboard_summary)

class A15DashboardTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row;self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
  self.today=date(2026,11,24)
  self.case=create_case(self.conn,{"case_title":"Jamabandi correction","case_type":"Correction","status":"Pending","next_hearing_date":"2026-12-03"})
  cur=self.conn.execute("INSERT INTO revenue_proceeding_plans(case_id,proceeding_type,forum_name,status,limitation_start_date,limitation_period_note,limitation_source_reference,limitation_reviewed_by,limitation_reviewed_date,limitation_due_date,limitation_caveat) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
   (self.case,"Correction","Revenue Officer","Working","2026-10-01","Entered period note","Act provision to verify","Reviewer","2026-11-20","2026-12-01","Verify exclusions and current rules"))
  self.proceeding=cur.lastrowid
  self.conn.execute("INSERT INTO revenue_proceeding_events(proceeding_id,event_date,event_type,title,next_action,deadline_date,source_reference,status) VALUES(?,?,?,?,?,?,?,?)",
   (self.proceeding,"2026-11-01","Filing","Submit certified copy","Obtain copy","2026-11-20","Order sheet","Open"))
  self.conn.execute("INSERT INTO revenue_proceeding_events(proceeding_id,event_date,event_type,title,next_action,deadline_date,source_reference,status) VALUES(?,?,?,?,?,?,?,?)",
   (self.proceeding,"2026-11-02","Hearing","Next hearing prep","Prepare file","2026-12-01","Order sheet","Open"))
  self.conn.execute("INSERT INTO revenue_proceeding_steps(proceeding_id,step_title,description,step_status,target_date,source_reference,verification_status) VALUES(?,?,?,?,?,?,?)",
   (self.proceeding,"Obtain certified copy","Apply at record room","Not started","2026-11-26","Order reference","unverified"))
  self.conn.execute("INSERT INTO revenue_case_evidence(case_id,evidence_title,verification_status) VALUES(?,?,?)",(self.case,"Jamabandi copy","unverified"))
  self.conn.commit()
 def tearDown(self):self.conn.close()
 def test_schema_and_case_rollup(self):
  self.assertGreaterEqual(CURRENT_SCHEMA_VERSION,14)
  row=case_dashboard_rows(self.conn,self.today)[0]
  self.assertEqual(row["case_id"],self.case);self.assertEqual(row["evidence_review_count"],1)
  self.assertEqual(row["active_proceedings"],1);self.assertEqual(row["outstanding_steps"],1)
  self.assertEqual(row["past_recorded_deadlines"],1)
 def test_hearings_and_recorded_deadline_classification(self):
  self.assertEqual(len(upcoming_hearings(self.conn,self.today)),1)
  rows=recorded_deadlines(self.conn,self.today)
  self.assertEqual(len(rows),2);self.assertEqual(rows[0]["deadline_date"],"2026-11-20")
 def test_outstanding_steps(self):
  self.assertEqual(len(outstanding_steps(self.conn)),1)
  self.conn.execute("UPDATE revenue_proceeding_steps SET step_status='Completed'");self.conn.commit()
  self.assertEqual(len(outstanding_steps(self.conn)),0)
 def test_limitation_is_manual_record_only(self):
  rows=manually_recorded_limitation_reviews(self.conn,self.today)
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]["limitation_due_date"],"2026-12-01")
  self.assertEqual(rows[0]["limitation_source_reference"],"Act provision to verify")
  # The service reports entered fields; it does not calculate a deadline.
 def test_summary_counts(self):
  s=dashboard_summary(self.conn,self.today)
  self.assertEqual(s["total_cases"],1);self.assertEqual(s["upcoming_hearings"],1)
  self.assertEqual(s["past_recorded_deadlines"],1);self.assertEqual(s["unreviewed_evidence"],1)

if __name__=="__main__":unittest.main()
