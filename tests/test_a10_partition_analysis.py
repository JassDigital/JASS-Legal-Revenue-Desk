import sqlite3
import unittest
from app.database.migrations import migrate
from app.services.revenue_records_service import add_record_set,add_entry
from app.services.revenue_partition_service import (create_plan,get_plan,update_plan,delete_plan,analyse_ownership,
 add_allocation,list_allocations,delete_allocation,analyse_plan,build_partition_report)

class A10PartitionTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:");self.conn.row_factory=sqlite3.Row
  self.conn.execute("PRAGMA foreign_keys=ON");migrate(self.conn)
  self.rid=add_record_set(self.conn,{"record_type":"Jamabandi","record_year":"2021-22","district":"Sirsa","tehsil":"Dabwali","village":"Village X","verification_status":"source_checked"})
  self.add_entry("10//2","Owner A",4,1,2);self.add_entry("10//2","Owner B",4,1,2)
  self.plan=create_plan(self.conn,{"plan_title":"Proposed partition","record_set_id":self.rid,"plan_status":"Working","basis_notes":"Jamabandi 2021-22","assumptions":"For discussion only"})
 def tearDown(self):self.conn.close()
 def add_entry(self,khasra,owner,area,num,den):
  add_entry(self.conn,self.rid,{"khewat_number":"5","khata_number":"10","khatauni_number":"15","khasra_number":khasra,"owner_name":owner,"parent_name":"","area_value":area,"area_unit":"acre","share_numerator":num,"share_denominator":den,"entry_notes":""})
 def test_schema_v10(self):
  self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],10)
  names={r["name"] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  self.assertTrue({"revenue_partition_plans","revenue_partition_allocations"}.issubset(names))
 def test_ownership_analysis(self):
  rs,khasras,owners,flags=analyse_ownership(self.conn,self.rid)
  self.assertEqual(khasras[0]["share_status"],"Shares total 100%")
  self.assertAlmostEqual(owners["Owner A"]["entitlement_acres"],2)
  self.assertFalse(flags)
 def test_share_shortfall_flag(self):
  rid=add_record_set(self.conn,{"record_type":"Jamabandi","record_year":"2016-17","district":"Sirsa","tehsil":"Dabwali","village":"Other village"})
  add_entry(self.conn,rid,{"khewat_number":"5","khata_number":"10","khatauni_number":"15","khasra_number":"20//1","owner_name":"Owner C","parent_name":"","area_value":2,"area_unit":"acre","share_numerator":1,"share_denominator":4,"entry_notes":""})
  _,rows,_,flags=analyse_ownership(self.conn,rid)
  self.assertTrue(any("less than 1" in x.lower() for x in flags))
 def test_allocation_reconciliation_and_report(self):
  add_allocation(self.conn,self.plan,{"khasra_number":"10//2","co_sharer_name":"Owner A","proposed_area":2,"area_unit":"acre","proposed_share_numerator":1,"proposed_share_denominator":2,"location_or_quality_notes":"North side"})
  add_allocation(self.conn,self.plan,{"khasra_number":"10//2","co_sharer_name":"Owner B","proposed_area":2,"area_unit":"acre","proposed_share_numerator":1,"proposed_share_denominator":2})
  plan,rows,flags=analyse_plan(self.conn,self.plan)
  self.assertIn("matches",rows[0]["comparison"])
  self.assertFalse(flags)
  report=build_partition_report(self.conn,self.plan)
  self.assertIn("PARTITION WORKING STATEMENT",report);self.assertIn("not a partition order",report)
 def test_excess_proposed_area_flag(self):
  add_allocation(self.conn,self.plan,{"khasra_number":"10//2","co_sharer_name":"Owner A","proposed_area":5,"area_unit":"acre"})
  _,rows,flags=analyse_plan(self.conn,self.plan)
  self.assertTrue(any("exceeds source" in x for x in flags))
 def test_plan_update_delete_cascades(self):
  add_allocation(self.conn,self.plan,{"khasra_number":"10//2","co_sharer_name":"Owner A","proposed_area":1,"area_unit":"acre"})
  update_plan(self.conn,self.plan,{"plan_title":"Updated plan","plan_status":"For review","basis_notes":"Updated","assumptions":"Assumption"})
  self.assertEqual(get_plan(self.conn,self.plan)["plan_title"],"Updated plan")
  delete_plan(self.conn,self.plan)
  self.assertEqual(len(list_allocations(self.conn,self.plan)),0)
 def test_delete_single_allocation(self):
  add_allocation(self.conn,self.plan,{"khasra_number":"10//2","co_sharer_name":"Owner A","proposed_area":1,"area_unit":"acre"})
  aid=list_allocations(self.conn,self.plan)[0]["allocation_id"];delete_allocation(self.conn,aid)
  self.assertEqual(len(list_allocations(self.conn,self.plan)),0)

if __name__=="__main__":unittest.main()
