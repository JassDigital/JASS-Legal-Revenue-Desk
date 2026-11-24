import sqlite3,unittest
from app.database.migrations import migrate,CURRENT_SCHEMA_VERSION
from app.services.revenue_case_service import create_case
from app.services.revenue_records_service import add_record_set,add_entry,add_mutation
from app.services.ownership_evidence_workspace import (list_villages,ownership_history,mutation_history,
 compare_ownership_years,evidence_trace,add_review_item,update_review_item,delete_review_item,
 list_review_items,build_ownership_history_report)

class A17OwnershipEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row;self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
  self.case=create_case(self.conn,{"case_title":"Inheritance and mutation dispute","case_type":"Mutation","status":"Pending","village":"Tosham","tehsil":"Tosham","district":"Bhiwani"})
  self.doc=self.conn.execute("INSERT INTO documents(document_title,document_type,original_filename,stored_path,file_hash,mime_type,extraction_status,extracted_text) VALUES(?,?,?,?,?,?,?,?)",("Jamabandi 2020","Revenue Record","jamabandi.pdf","/tmp/jamabandi.pdf","hash1","application/pdf","extracted","Owner Ramesh Khasra 17/2")).lastrowid
  self.old=add_record_set(self.conn,{"case_id":self.case,"record_type":"Jamabandi","record_year":"2020-21","district":"Bhiwani","tehsil":"Tosham","village":"Tosham","source_reference":"Jamabandi volume 1","source_document_id":self.doc,"verification_status":"copy_compared"})
  self.new=add_record_set(self.conn,{"case_id":self.case,"record_type":"Jamabandi","record_year":"2024-25","district":"Bhiwani","tehsil":"Tosham","village":"Tosham","source_reference":"Jamabandi volume 2","verification_status":"unverified"})
  add_entry(self.conn,self.old,{"khasra_number":"17/2","owner_name":"Ramesh Kumar","parent_name":"Mohan","area_value":2,"area_unit":"acre","share_numerator":1,"share_denominator":2,"khata_number":"88"})
  add_entry(self.conn,self.old,{"khasra_number":"17/2","owner_name":"Suresh Kumar","parent_name":"Mohan","area_value":2,"area_unit":"acre","share_numerator":1,"share_denominator":2,"khata_number":"88"})
  add_entry(self.conn,self.new,{"khasra_number":"17/2","owner_name":"Ramesh Kumar","parent_name":"Mohan","area_value":2,"area_unit":"acre","share_numerator":1,"share_denominator":1,"khata_number":"99"})
  add_entry(self.conn,self.new,{"khasra_number":"17/2","owner_name":"Anita Devi","parent_name":"Mohan","area_value":2,"area_unit":"acre","share_numerator":0,"share_denominator":1,"khata_number":"99"})
  add_mutation(self.conn,{"record_set_id":self.new,"case_id":self.case,"mutation_number":"42","mutation_date":"2023-06-12","mutation_type":"Inheritance","khasra_numbers":"17/2, 18/1","from_party":"Suresh Kumar","to_party":"Ramesh Kumar","status":"Entered","source_reference":"Mutation order page 3"})
  self.conn.execute("INSERT INTO revenue_case_document_links(case_id,document_id,link_type,page_reference,relevance_note,verification_status) VALUES(?,?,?,?,?,?)",(self.case,self.doc,"Ownership record","Pages 1-4","Earlier Jamabandi snapshot","copy_compared"));self.conn.commit()
 def tearDown(self):self.conn.close()
 def test_schema_and_village_discovery(self):
  self.assertGreaterEqual(CURRENT_SCHEMA_VERSION,16)
  self.assertEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],16)
  self.assertEqual(list_villages(self.conn,self.case)[0]["village"],"Tosham")
 def test_ownership_history_filter_and_year_order(self):
  rows=ownership_history(self.conn,"Tosham",self.case,"17/2")
  self.assertEqual(len(rows),4);self.assertEqual(rows[0]["record_year"],"2020-21");self.assertEqual(rows[-1]["record_year"],"2024-25")
 def test_cross_year_owner_comparison(self):
  a,b,rows=compare_ownership_years(self.conn,"Tosham",self.old,self.new)
  by={(r["khasra"],r["owner"]):r for r in rows}
  self.assertEqual(by[("17/2","Ramesh Kumar")]["status"],"Changed: Khata, Share denominator")
  self.assertEqual(by[("17/2","Suresh Kumar")]["status"],"Absent from later snapshot")
  self.assertEqual(by[("17/2","Anita Devi")]["status"],"Added in later snapshot")
 def test_comparison_rejects_different_village(self):
  other=add_record_set(self.conn,{"record_type":"Jamabandi","record_year":"2024","village":"Other village"})
  with self.assertRaises(ValueError):compare_ownership_years(self.conn,"Tosham",self.old,other)
 def test_mutation_history_and_khasra_token_filter(self):
  rows=mutation_history(self.conn,"Tosham",self.case,"17/2")
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]["mutation_number"],"42")
  self.assertEqual(len(mutation_history(self.conn,"Tosham",self.case,"7/2")),0)
 def test_source_trace_links_record_set_and_case_document(self):
  rows=evidence_trace(self.conn,"Tosham",self.case)
  self.assertTrue(any(r["document_title"]=="Jamabandi 2020" and r["page_reference"]=="Pages 1-4" for r in rows))
 def test_review_register_crud(self):
  rid=add_review_item(self.conn,self.case,{"village":"Tosham","khasra_number":"17/2","owner_name":"Ramesh Kumar","observation":"Share changed between snapshots.","question_for_review":"Locate mutation order and verify parties.","page_reference":"Jamabandi 2024-25 p. 6"})
  self.assertEqual(len(list_review_items(self.conn,self.case)),1)
  update_review_item(self.conn,rid,{"review_type":"Discrepancy","observation":"Confirmed difference to investigate","question_for_review":"Compare mutation register","page_reference":"p. 6","review_status":"Under review","verification_status":"needs_review","resolution_note":"Awaiting certified order"})
  self.assertEqual(list_review_items(self.conn,self.case)[0]["review_status"],"Under review")
  delete_review_item(self.conn,rid);self.assertEqual(len(list_review_items(self.conn,self.case)),0)
 def test_report_contains_trace_and_limitations(self):
  report=build_ownership_history_report(self.conn,"Tosham",self.case,"17/2")
  self.assertIn("2020-21",report);self.assertIn("Mutation 42",report);self.assertIn("Pages 1-4",report)
  self.assertIn("does not prove the legal cause",report)
 def test_case_delete_cascades_review_items(self):
  rid=add_review_item(self.conn,self.case,{"observation":"Test discrepancy"})
  self.conn.execute("DELETE FROM revenue_cases WHERE case_id=?",(self.case,));self.conn.commit()
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM revenue_ownership_review_items WHERE review_item_id=?",(rid,)).fetchone()[0],0)

if __name__=="__main__":unittest.main()
