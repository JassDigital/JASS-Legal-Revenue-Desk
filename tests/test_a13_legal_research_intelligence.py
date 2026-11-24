import sqlite3, unittest
from app.database.migrations import migrate,CURRENT_SCHEMA_VERSION
from app.services.revenue_case_service import create_case,delete_case
from app.services.legal_source_verification import save_source
from app.services.legal_research_intelligence import *

class A13ResearchTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row;self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
  self.case_id=create_case(self.conn,{"case_title":"Mutation appeal","case_type":"Mutation","status":"Preparing","priority":"Normal","district":"Sirsa","tehsil":"Dabwali","village":"Village A"})
  mid=self.conn.execute("INSERT INTO revenue_law_materials(title,material_type,jurisdiction,description) VALUES('Haryana Land Revenue Act','Principal Act','Haryana','Land revenue provisions')").lastrowid
  sec=self.conn.execute("INSERT INTO revenue_law_sections(material_id,section_number,heading,section_text,verification_status) VALUES(?,?,?,?,?)",(mid,"16","Appeals","Appeal provision text","copy_compared")).lastrowid
  self.source_id=save_source(self.conn,{"material_id":mid,"section_id":sec,"source_title":"Haryana Land Revenue Act — section 16","source_type":"Act","publisher":"Haryana Gazette","jurisdiction":"Haryana","source_identifier":"Act text copy","officiality":"official_primary","legal_status":"uncertain","verification_status":"copy_compared","verified_by":"Reviewer","verified_date":"2026-11-24","verification_notes":"Check latest amendments."})
  self.jid=self.conn.execute("INSERT INTO judgments(case_title,citation,court_name,decision_date,full_text,verification_status) VALUES(?,?,?,?,?,?)",("Example v Example","2024 PLR 100","Punjab and Haryana High Court","2024-03-10","Mutation appeal and limitation discussion","unverified")).lastrowid
  self.jsource=save_source(self.conn,{"judgment_id":self.jid,"source_title":"Example v Example judgment","source_type":"Judgment","publisher":"Court source","jurisdiction":"Haryana","source_identifier":"2024 PLR 100","officiality":"court_hosted","legal_status":"unverified","verification_status":"source_located"})
 def tearDown(self):self.conn.close()
 def test_schema_v13(self):
  self.assertGreaterEqual(CURRENT_SCHEMA_VERSION,13)
  self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],13)
  names={r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  self.assertTrue({"legal_research_bundles","legal_research_issues","legal_research_arguments","legal_research_issue_sources"}.issubset(names))
 def test_search_across_linked_statute_and_judgment_text(self):
  rows=search_research_sources(self.conn,"Appeals")
  self.assertTrue(any(r["source_record_id"]==self.source_id for r in rows))
  rows=search_research_sources(self.conn,"limitation")
  self.assertTrue(any(r["source_record_id"]==self.jsource for r in rows))
  self.assertEqual(search_research_sources(self.conn,"appeals","copy_compared")[0]["source_record_id"],self.source_id)
 def test_bundle_issue_arguments_sources_and_report(self):
  bid=create_bundle(self.conn,{"case_id":self.case_id,"title":"Mutation appeal research","research_question":"What is the appropriate remedy?","scope_notes":"Haryana law only"})
  iid=create_issue(self.conn,bid,{"issue_title":"Maintainability and limitation","material_facts":"Order passed; copy date needs proof","legal_question":"Which remedy and time limit apply?","provisional_view":"Open pending current law review"})
  attach_source(self.conn,iid,self.source_id,{"position":"Supports","pinpoint":"Section 16","proposition":"Statutory appeal route to verify","verification_status":"copy_compared"})
  attach_source(self.conn,iid,self.jsource,{"position":"Contrary","pinpoint":"Paragraph 12","proposition":"Potential adverse treatment","relevance_note":"Check later history"})
  add_argument(self.conn,iid,{"argument_type":"Proposed","argument_text":"The order may be appealable subject to the governing version and limitation.","status":"Needs research"})
  self.assertEqual(len(issue_sources(self.conn,iid)),2);self.assertEqual(len(arguments(self.conn,iid)),1)
  report=build_bundle_report(self.conn,bid)
  for term in ["SUPPORTING","Contrary","Section 16","Paragraph 12","does not establish authenticity","absence from results does not mean"]:
   self.assertIn(term,report)
 def test_issue_delete_cascades_children(self):
  bid=create_bundle(self.conn,{"title":"Bundle"});iid=create_issue(self.conn,bid,{"issue_title":"Issue"})
  attach_source(self.conn,iid,self.source_id,{})
  add_argument(self.conn,iid,{"argument_text":"Argument"})
  delete_issue(self.conn,iid)
  self.assertEqual(len(issue_sources(self.conn,iid)),0);self.assertEqual(len(arguments(self.conn,iid)),0)
 def test_bundle_delete_cascades_issues(self):
  bid=create_bundle(self.conn,{"title":"Bundle"});create_issue(self.conn,bid,{"issue_title":"Issue"})
  delete_bundle(self.conn,bid);self.assertEqual(len(bundle_issues(self.conn,bid)),0)
 def test_case_delete_cascades_case_linked_bundle(self):
  bid=create_bundle(self.conn,{"case_id":self.case_id,"title":"Case bundle"})
  delete_case(self.conn,self.case_id)
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM legal_research_bundles WHERE bundle_id=?",(bid,)).fetchone()[0],0)
 def test_duplicate_source_attachment_idempotent(self):
  bid=create_bundle(self.conn,{"title":"Bundle"});iid=create_issue(self.conn,bid,{"issue_title":"Issue"})
  attach_source(self.conn,iid,self.source_id,{})
  attach_source(self.conn,iid,self.source_id,{})
  self.assertEqual(len(issue_sources(self.conn,iid)),1)

if __name__=="__main__":unittest.main()
