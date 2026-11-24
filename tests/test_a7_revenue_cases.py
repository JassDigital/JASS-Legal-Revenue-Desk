import sqlite3
import unittest
from app.database.migrations import migrate
from app.services.revenue_case_service import (create_case,update_case,list_cases,case_detail,add_party,parties,
    add_property,properties,add_event,events,add_evidence,evidence,add_issue,issues,delete_case)

class A7RevenueCaseTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(":memory:")
        self.conn.row_factory=sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        migrate(self.conn)
    def tearDown(self):self.conn.close()
    def new_case(self):
        return create_case(self.conn,{"case_title":"Mutation dispute — Village X","case_type":"Mutation","status":"Preparing","priority":"High","district":"Sirsa","tehsil":"Dabwali","village":"Village X"})
    def test_schema_v7(self):
        self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],7)
        names={r["name"] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"revenue_cases","revenue_case_parties","revenue_case_properties","revenue_case_events","revenue_case_evidence","revenue_case_issues"}.issubset(names))
    def test_create_filter_update(self):
        cid=self.new_case()
        self.assertEqual(len(list_cases(self.conn,"Village X")),1)
        self.assertEqual(len(list_cases(self.conn,"","Pending")),0)
        update_case(self.conn,cid,{"case_title":"Updated title","case_type":"Appeal","status":"Pending","priority":"Normal"})
        self.assertEqual(case_detail(self.conn,cid)["case_title"],"Updated title")
    def test_case_components(self):
        cid=self.new_case()
        add_party(self.conn,cid,{"party_name":"Person A","role":"Applicant","address":"Village X","contact_notes":"","representative":"Self"})
        add_property(self.conn,cid,{"village":"Village X","tehsil":"Dabwali","district":"Sirsa","hadbast_number":"42","jamabandi_year":"2021-22","khata_number":"12","khatauni_number":"18","khasra_numbers":"10//2","area":"2 acres","ownership_share":"1/2","land_description":"Agricultural land"})
        add_event(self.conn,cid,{"event_date":"2026-11-24","event_type":"Hearing","title":"First hearing","details":"Notice issued","next_action":"File reply"})
        add_evidence(self.conn,cid,{"document_id":None,"evidence_title":"Jamabandi copy","evidence_type":"Revenue record","document_reference":"Page 3","relevance_notes":"Ownership entry","verification_status":"unverified"})
        add_issue(self.conn,cid,{"issue_title":"Whether mutation is sustainable","facts":"Disputed entry","legal_question":"Whether procedure was followed","proposed_argument":"Challenge entry","relevant_law":"Punjab Land Revenue Act","status":"Open"})
        self.assertEqual(parties(self.conn,cid)[0]["party_name"],"Person A")
        self.assertEqual(properties(self.conn,cid)[0]["khasra_numbers"],"10//2")
        self.assertEqual(events(self.conn,cid)[0]["title"],"First hearing")
        self.assertEqual(evidence(self.conn,cid)[0]["evidence_title"],"Jamabandi copy")
        self.assertEqual(issues(self.conn,cid)[0]["issue_title"],"Whether mutation is sustainable")
    def test_delete_case_cascades(self):
        cid=self.new_case()
        add_party(self.conn,cid,{"party_name":"Person A","role":"Applicant","address":"","contact_notes":"","representative":""})
        delete_case(self.conn,cid)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM revenue_case_parties").fetchone()[0],0)

if __name__=="__main__":unittest.main()
