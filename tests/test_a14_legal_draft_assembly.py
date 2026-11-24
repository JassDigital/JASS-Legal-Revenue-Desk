import sqlite3,unittest
from app.database.migrations import migrate,CURRENT_SCHEMA_VERSION
from app.services.revenue_case_service import create_case
from app.services.revenue_drafting_service import get_draft,delete_draft
from app.services.legal_source_verification import save_source,delete_source
from app.services.legal_research_intelligence import create_bundle,create_issue,attach_source,add_argument
from app.services.legal_draft_assembly import *

class A14DraftAssemblyTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row;self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
  self.case=create_case(self.conn,{"case_title":"Mutation case","case_type":"Mutation","status":"Preparing","priority":"Normal"})
  self.other=create_case(self.conn,{"case_title":"Other case","case_type":"Appeal","status":"Preparing","priority":"Normal"})
  self.source=save_source(self.conn,{"source_title":"Haryana Revenue Act — section 16","source_type":"Act","publisher":"Gazette","jurisdiction":"Haryana","source_identifier":"Act reference 16","source_url":"https://example.invalid/act","officiality":"official_primary","legal_status":"uncertain","verification_status":"copy_compared"})
  self.bundle=create_bundle(self.conn,{"case_id":self.case,"title":"Mutation appeal research","research_question":"What remedy may be available?","scope_notes":"Haryana only"})
  self.issue=create_issue(self.conn,self.bundle,{"issue_title":"Appeal route","material_facts":"Order date must be verified.","legal_question":"Which appeal provision applies?","provisional_view":"Subject to version and limitation review."})
  attach_source(self.conn,self.issue,self.source,{"position":"Supports","pinpoint":"Section 16","proposition":"Potential appeal route; verify current text."})
  attach_source(self.conn,self.issue,self.source,{"position":"Contrary","pinpoint":"Section 16(2)","proposition":"Potential limitation qualification."})
  add_argument(self.conn,self.issue,{"argument_type":"Proposed","argument_text":"The order may be appealable if the governing provision applies.","status":"Needs research","notes":"Verify forum and limitation."})
 def tearDown(self):self.conn.close()
 def test_schema_v14(self):
  self.assertGreaterEqual(CURRENT_SCHEMA_VERSION,14)
  self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],14)
  cols={r["name"] for r in self.conn.execute("PRAGMA table_info(revenue_case_drafts)")}
  self.assertIn("research_bundle_id",cols)
  self.assertTrue(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='revenue_case_draft_sources'").fetchone())
 def test_draft_creation_preserves_issue_content_and_citations(self):
  did=create_draft_from_bundle(self.conn,self.case,self.bundle,"Appeal","Working appeal draft")
  d=get_draft(self.conn,did)
  self.assertEqual(d["research_bundle_id"],self.bundle)
  self.assertIn("ISSUE 1: Appeal route",d["body"])
  self.assertIn("The order may be appealable",d["body"])
  self.assertEqual(len(draft_source_register(self.conn,did)),2)
  export=build_draft_export(self.conn,did)
  self.assertIn("SOURCE & PINPOINT SCHEDULE",export)
  self.assertIn("Section 16(2)",export)
  self.assertIn("verify current text",export)
 def test_general_bundle_allowed_but_wrong_case_bundle_rejected(self):
  general=create_bundle(self.conn,{"title":"General Haryana research"})
  did=create_draft_from_bundle(self.conn,self.case,general,"Other","General draft")
  self.assertIsNotNone(get_draft(self.conn,did))
  with self.assertRaises(ValueError):create_draft_from_bundle(self.conn,self.other,self.bundle,"Appeal","Wrong case")
 def test_source_deletion_keeps_draft_citation_snapshot(self):
  did=create_draft_from_bundle(self.conn,self.case,self.bundle,"Appeal","Snapshot draft")
  delete_source(self.conn,self.source)
  rows=draft_source_register(self.conn,did)
  self.assertEqual(len(rows),2)
  self.assertEqual(rows[0]["source_title_snapshot"],"Haryana Revenue Act — section 16")
  self.assertIsNone(rows[0]["source_record_id"])
 def test_draft_delete_cascades_citation_snapshots(self):
  did=create_draft_from_bundle(self.conn,self.case,self.bundle,"Appeal","Delete draft")
  delete_draft(self.conn,did)
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM revenue_case_draft_sources WHERE draft_id=?",(did,)).fetchone()[0],0)
 def test_empty_title_rejected(self):
  with self.assertRaises(ValueError):create_draft_from_bundle(self.conn,self.case,self.bundle,"Appeal"," ")
 def test_eligible_bundles_case_and_general_only(self):
  create_bundle(self.conn,{"case_id":self.other,"title":"Different case"})
  create_bundle(self.conn,{"title":"General"})
  ids={r["bundle_id"] for r in eligible_bundles(self.conn,self.case)}
  self.assertEqual(ids,{self.bundle,self.conn.execute("SELECT bundle_id FROM legal_research_bundles WHERE case_id IS NULL").fetchone()[0]})

if __name__=="__main__":unittest.main()
