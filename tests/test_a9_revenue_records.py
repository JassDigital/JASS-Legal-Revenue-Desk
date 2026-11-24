import sqlite3
import unittest
from app.database.migrations import migrate
from app.services.revenue_records_service import (add_record_set,add_entry,record_sets,entries,add_mutation,
 mutations,area_in_acres,share_area,compare_record_sets,record_integrity_flags,delete_record_set)

class A9RevenueRecordsTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row
  self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
 def tearDown(self):self.conn.close()
 def make_set(self,year):
  return add_record_set(self.conn,{"record_type":"Jamabandi","record_year":year,"district":"Sirsa","tehsil":"Dabwali","village":"Village X","verification_status":"source_checked"})
 def add(self,rid,owner="Person A",area=2,num=1,den=2):
  add_entry(self.conn,rid,{"khewat_number":"10","khata_number":"12","khatauni_number":"18","khasra_number":"10//2","owner_name":owner,"parent_name":"","area_value":area,"area_unit":"acre","share_numerator":num,"share_denominator":den,"entry_notes":""})
 def test_schema_v9(self):
  self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],9)
  tables={r["name"] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  self.assertTrue({"revenue_record_sets","revenue_record_entries","revenue_mutation_records"}.issubset(tables))
 def test_record_set_and_entries(self):
  rid=self.make_set("2021-22");self.add(rid)
  self.assertEqual(len(record_sets(self.conn)),1);self.assertEqual(entries(self.conn,rid)[0]["owner_name"],"Person A")
 def test_area_and_share_calculations(self):
  self.assertAlmostEqual(area_in_acres(8,"kanal"),1)
  self.assertAlmostEqual(area_in_acres(160,"marla"),1)
  self.assertAlmostEqual(share_area(2,"acre",1,4),0.5)
 def test_mutation_history(self):
  rid=self.make_set("2021-22")
  add_mutation(self.conn,{"record_set_id":rid,"mutation_number":"123","mutation_date":"2022-05-01","mutation_type":"Inheritance","khasra_numbers":"10//2","from_party":"Parent","to_party":"Child","status":"Sanctioned","area_unit":"acre"})
  self.assertEqual(mutations(self.conn)[0]["mutation_number"],"123")
 def test_compare_snapshots(self):
  a=self.make_set("2016-17");b=self.make_set("2021-22")
  self.add(a);self.add(b,area=3,num=3,den=4)
  left,right,rows=compare_record_sets(self.conn,a,b)
  self.assertIn("Changed",rows[0]["status"])
 def test_integrity_flag_when_shares_exceed_one(self):
  rid=self.make_set("2021-22");self.add(rid,"Person A",2,3,4);self.add(rid,"Person B",2,3,4)
  self.assertTrue(any("exceeding 1" in x for x in record_integrity_flags(self.conn,rid)))
 def test_delete_snapshot_cascades_entries(self):
  rid=self.make_set("2021-22");self.add(rid);delete_record_set(self.conn,rid)
  self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM revenue_record_entries").fetchone()[0],0)

if __name__=="__main__":unittest.main()
