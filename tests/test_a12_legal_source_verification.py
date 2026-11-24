import sqlite3, tempfile, unittest
from pathlib import Path
from app.database.migrations import migrate,CURRENT_SCHEMA_VERSION
from app.services.legal_source_verification import *

class A12SourceTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row;self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
  cur=self.conn.execute("INSERT INTO revenue_law_materials(title,material_type,jurisdiction) VALUES('Test Act','Principal Act','Haryana')");self.mid=cur.lastrowid
  cur=self.conn.execute("INSERT INTO revenue_law_sections(material_id,section_number,heading,section_text) VALUES(?,?,?,?)",(self.mid,"12","Appeal","Sample text"));self.secid=cur.lastrowid
 def tearDown(self):self.conn.close()
 def source(self):
  return {"material_id":self.mid,"section_id":self.secid,"source_title":"Test Act, section 12 official Gazette copy","source_type":"Act","publisher":"Government Gazette","jurisdiction":"Haryana","source_url":"https://example.invalid/gazette.pdf","source_identifier":"Gazette Part III, page 10","publication_date":"2025-01-02","retrieval_date":"2026-11-24","effective_from":"2025-01-02","effective_to":"","officiality":"official_primary","legal_status":"unverified","verification_status":"source_located","verified_by":"Reviewer","verified_date":"2026-11-24","hash_sha256":"","source_snapshot_path":"","verification_notes":"Individual issue located; commencement to confirm."}
 def test_schema_v12(self):
  self.assertGreaterEqual(CURRENT_SCHEMA_VERSION,12)
  self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],12)
  names={r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  self.assertTrue({"legal_source_records","legal_source_versions","legal_citation_links"}.issubset(names))
 def test_source_create_edit_search(self):
  sid=save_source(self.conn,self.source());self.assertEqual(get_source(self.conn,sid)["source_title"],self.source()["source_title"])
  self.assertEqual(len(source_records(self.conn,"official Gazette")),1)
  v=self.source();v["verification_status"]="legally_reviewed";v["legal_status"]="in_force_confirmed";save_source(self.conn,v,sid)
  self.assertEqual(get_source(self.conn,sid)["legal_status"],"in_force_confirmed")
 def test_versions_and_citations(self):
  sid=save_source(self.conn,self.source())
  add_source_version(self.conn,sid,{"version_label":"As amended from 2025","instrument_reference":"Amendment Act No. X","effective_from":"2025-01-02","source_reference":"Gazette Part III, page 10","change_summary":"Section 12 amended","verification_status":"source_located"})
  self.assertEqual(len(source_versions(self.conn,sid)),1)
  add_citation(self.conn,sid,{"target_type":"Revenue case","target_label":"Mutation appeal case","citation_kind":"Supports","pinpoint":"Section 12; Gazette p.10","proposition":"The appeal route requires examination under the verified version.","excerpt":"Short excerpt","verification_status":"unverified"})
  self.assertEqual(len(citations(self.conn,sid)),1)
  report=build_source_report(self.conn,sid)
  self.assertIn("VERSION / AMENDMENT HISTORY",report);self.assertIn("CITATION LINKS",report);self.assertIn("does not itself establish authenticity",report)
 def test_snapshot_hash_and_path(self):
  sid=save_source(self.conn,self.source())
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"gazette.pdf";path.write_bytes(b"sample snapshot bytes")
   digest=verify_snapshot(self.conn,sid,path,Path(d)/"preserved")
   self.assertEqual(len(digest),64);self.assertEqual(get_source(self.conn,sid)["hash_sha256"],digest)
   self.assertEqual(sha256_file(path),digest)
   self.assertTrue(Path(get_source(self.conn,sid)["source_snapshot_path"]).is_file())
 def test_invalid_date_rejected(self):
  v=self.source();v["publication_date"]="02-01-2025"
  with self.assertRaises(ValueError):save_source(self.conn,v)
 def test_missing_citation_proposition_rejected(self):
  sid=save_source(self.conn,self.source())
  with self.assertRaises(ValueError):add_citation(self.conn,sid,{"target_label":"My case"})
 def test_source_delete_cascades_history_and_citations(self):
  sid=save_source(self.conn,self.source());add_source_version(self.conn,sid,{"version_label":"Original"})
  add_citation(self.conn,sid,{"target_label":"Case","proposition":"Proposition"})
  delete_source(self.conn,sid)
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM legal_source_versions").fetchone()[0],0)
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM legal_citation_links").fetchone()[0],0)

if __name__=="__main__":unittest.main()
