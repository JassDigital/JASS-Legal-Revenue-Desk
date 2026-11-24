import sqlite3,unittest
from app.database.migrations import migrate,CURRENT_SCHEMA_VERSION
from app.services.revenue_case_service import create_case
from app.services.revenue_document_intelligence import (search_documents,document_detail,save_document_metadata,
 add_case_document_link,list_case_document_links,delete_case_document_link,build_case_evidence_index)

class A16DocumentIntelligenceTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row;self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
  self.case=create_case(self.conn,{"case_title":"Mutation dispute","case_type":"Mutation","status":"Preparing"})
  self.party=self.conn.execute("INSERT INTO revenue_case_parties(case_id,party_name,role) VALUES(?,?,?)",(self.case,"Ramesh Kumar","Applicant")).lastrowid
  self.issue=self.conn.execute("INSERT INTO revenue_case_issues(case_id,issue_title) VALUES(?,?)",(self.case,"Mutation entry challenged")).lastrowid
  self.doc=self.conn.execute("""INSERT INTO documents(document_title,document_type,original_filename,stored_path,file_hash,mime_type,page_count,extraction_status,extracted_text)
   VALUES(?,?,?,?,?,?,?,?,?)""",("Mutation order 42","Revenue Record","order42.pdf","/tmp/order42.pdf","abc123","application/pdf",4,"extracted","Mutation order dated 2024-04-12 records Khasra 17/2 and Khata 88." )).lastrowid
  self.conn.commit()
 def tearDown(self):self.conn.close()
 def test_schema_and_fts_index(self):
  self.assertGreaterEqual(CURRENT_SCHEMA_VERSION,15)
  self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],15)
  rows=search_documents(self.conn,"Khasra 17/2")
  self.assertEqual([r["document_id"] for r in rows],[self.doc])
  self.assertIn("Khasra",rows[0]["excerpt"])
 def test_metadata_roundtrip_and_searchable_record_fields(self):
  save_document_metadata(self.conn,self.doc,{"record_date":"2024-04-12","issuing_authority":"Naib Tehsildar","record_reference":"Mutation No. 42","village":"Tosham","tehsil":"Tosham","district":"Bhiwani","khasra_numbers":"17/2","khata_number":"88","jamabandi_year":"2020-21","metadata_status":"copy_compared","page_notes":"Order copy, four pages."})
  row=document_detail(self.conn,self.doc)
  self.assertEqual(row["record_reference"],"Mutation No. 42")
  self.assertEqual(row["metadata_status"],"copy_compared")
  self.assertEqual(len(search_documents(self.conn,"Mutation No. 42")),1)
 def test_case_link_and_evidence_index(self):
  save_document_metadata(self.conn,self.doc,{"record_reference":"Mutation No. 42","village":"Tosham","khasra_numbers":"17/2"})
  link=add_case_document_link(self.conn,self.case,self.doc,{"party_id":self.party,"issue_id":self.issue,"link_type":"Mutation order","page_reference":"Pages 1–3","relevance_note":"Impugned mutation entry","verification_status":"copy_compared","notes":"Compare with original"})
  self.assertTrue(link)
  rows=list_case_document_links(self.conn,self.case)
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]["party_name"],"Ramesh Kumar")
  report=build_case_evidence_index(self.conn,self.case)
  self.assertIn("Mutation No. 42",report);self.assertIn("Pages 1–3",report);self.assertIn("Khasra: 17/2",report)
 def test_link_rejects_party_from_another_case(self):
  other=create_case(self.conn,{"case_title":"Other case","case_type":"Appeal","status":"Preparing"})
  other_party=self.conn.execute("INSERT INTO revenue_case_parties(case_id,party_name) VALUES(?,?)",(other,"Other party")).lastrowid
  with self.assertRaises(ValueError):
   add_case_document_link(self.conn,self.case,self.doc,{"party_id":other_party})
 def test_duplicate_link_is_idempotent(self):
  v={"party_id":self.party,"issue_id":self.issue,"link_type":"Evidence","page_reference":"Page 1"}
  first=add_case_document_link(self.conn,self.case,self.doc,v)
  second=add_case_document_link(self.conn,self.case,self.doc,v)
  self.assertEqual(first,second);self.assertEqual(len(list_case_document_links(self.conn,self.case)),1)
 def test_duplicate_unassigned_link_is_idempotent(self):
  v={"link_type":"Evidence","page_reference":"Page 2"}
  first=add_case_document_link(self.conn,self.case,self.doc,v)
  second=add_case_document_link(self.conn,self.case,self.doc,v)
  self.assertEqual(first,second);self.assertEqual(len(list_case_document_links(self.conn,self.case)),1)
 def test_delete_link_does_not_delete_document(self):
  link=add_case_document_link(self.conn,self.case,self.doc,{"link_type":"Evidence"})
  delete_case_document_link(self.conn,link)
  self.assertIsNotNone(document_detail(self.conn,self.doc))
  self.assertEqual(len(list_case_document_links(self.conn,self.case)),0)
 def test_fts_updates_when_extracted_text_changes(self):
  self.conn.execute("UPDATE documents SET extracted_text='Certified jamabandi copy for Khasra 91' WHERE document_id=?",(self.doc,));self.conn.commit()
  self.assertEqual(len(search_documents(self.conn,"jamabandi Khasra 91")),1)
  self.assertEqual(len(search_documents(self.conn,"dated 2024-04-12 records")),0)
 def test_document_delete_cascades_metadata_and_links(self):
  save_document_metadata(self.conn,self.doc,{"record_reference":"Mutation No. 42"})
  add_case_document_link(self.conn,self.case,self.doc,{"link_type":"Evidence"})
  self.conn.execute("DELETE FROM documents WHERE document_id=?",(self.doc,));self.conn.commit()
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM revenue_document_metadata WHERE document_id=?",(self.doc,)).fetchone()[0],0)
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM revenue_case_document_links WHERE document_id=?",(self.doc,)).fetchone()[0],0)
  self.assertEqual(len(search_documents(self.conn)),0)

if __name__=="__main__":unittest.main()
