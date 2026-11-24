import sqlite3
import unittest
from app.database.migrations import migrate
from app.services.revenue_case_service import create_case,add_party,add_evidence,add_issue
from app.services.revenue_drafting_service import (save_draft,list_drafts,get_draft,delete_draft,
    add_evidence_link,list_evidence_links,delete_evidence_link,build_case_report)

class A8DraftingStudioTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
        self.cid=create_case(self.conn,{"case_title":"Partition matter","case_type":"Partition","status":"Preparing","priority":"Normal","district":"Sirsa","tehsil":"Dabwali","village":"Test village","case_summary":"Partition of joint holding","strategy_notes":"Check record"})
        add_party(self.conn,self.cid,{"party_name":"Applicant A","role":"Applicant","address":"","contact_notes":"","representative":"Self"})
        add_evidence(self.conn,self.cid,{"document_id":None,"evidence_title":"Jamabandi 2021-22","evidence_type":"Revenue record","document_reference":"Khata 10","relevance_notes":"Co-sharer entries","verification_status":"source_checked"})
        add_issue(self.conn,self.cid,{"issue_title":"Mode of partition","facts":"Joint holding","legal_question":"How should shares be separated?","proposed_argument":"As per recorded shares","relevant_law":"Applicable revenue law","status":"Open"})
    def tearDown(self):self.conn.close()
    def test_schema_v8(self):
        self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],8)
        names={r["name"] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"revenue_case_drafts","revenue_case_evidence_links","revenue_case_report_log"}.issubset(names))
    def test_draft_create_update_delete_and_version(self):
        did=save_draft(self.conn,self.cid,{"draft_type":"Application","title":"Application for partition","body":"Draft text","status":"Working"})
        self.assertEqual(len(list_drafts(self.conn,self.cid)),1)
        save_draft(self.conn,self.cid,{"draft_type":"Application","title":"Application for partition","body":"Revised text","status":"For review"},did)
        self.assertEqual(get_draft(self.conn,did)["version"],2)
        self.assertEqual(get_draft(self.conn,did)["body"],"Revised text")
        delete_draft(self.conn,did);self.assertEqual(len(list_drafts(self.conn,self.cid)),0)
    def test_evidence_link_and_delete(self):
        eid=self.conn.execute("SELECT evidence_id FROM revenue_case_evidence WHERE case_id=?",(self.cid,)).fetchone()[0]
        pid=self.conn.execute("SELECT party_id FROM revenue_case_parties WHERE case_id=?",(self.cid,)).fetchone()[0]
        iid=self.conn.execute("SELECT issue_id FROM revenue_case_issues WHERE case_id=?",(self.cid,)).fetchone()[0]
        add_evidence_link(self.conn,eid,pid,iid,"Supports ownership background")
        links=list_evidence_links(self.conn,self.cid)
        self.assertEqual(links[0]["party_name"],"Applicant A")
        self.assertEqual(links[0]["issue_title"],"Mode of partition")
        delete_evidence_link(self.conn,links[0]["link_id"])
        self.assertEqual(len(list_evidence_links(self.conn,self.cid)),0)
    def test_report_contains_case_sections_and_disclaimer(self):
        report=build_case_report(self.conn,self.cid)
        for phrase in ["Partition matter","PARTIES","LAND / PROPERTY","CHRONOLOGY / HEARINGS","EVIDENCE REGISTER","ISSUES & ARGUMENTS","not legal advice"]:
            self.assertIn(phrase,report)
    def test_case_deletion_cascades_drafts(self):
        did=save_draft(self.conn,self.cid,{"draft_type":"Other","title":"Test","body":"x","status":"Working"})
        self.conn.execute("DELETE FROM revenue_cases WHERE case_id=?",(self.cid,));self.conn.commit()
        self.assertIsNone(get_draft(self.conn,did))

if __name__=="__main__":unittest.main()
