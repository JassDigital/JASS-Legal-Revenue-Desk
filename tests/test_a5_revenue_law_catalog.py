import sqlite3
import unittest
from app.database.migrations import migrate
from app.services.revenue_law_catalog import seed_revenue_law_catalog, search_materials

class A5RevenueLawCatalogTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(":memory:")
        self.conn.row_factory=sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        migrate(self.conn)
        seed_revenue_law_catalog(self.conn)
    def tearDown(self): self.conn.close()
    def test_schema_v5_and_seed_records(self):
        version=self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        self.assertGreaterEqual(version,5)
        self.assertGreaterEqual(self.conn.execute("SELECT COUNT(*) FROM revenue_law_materials").fetchone()[0],4)
    def test_search_finds_partition_amendment(self):
        rows=search_materials(self.conn,"partition")
        titles=[r["title"] for r in rows]
        self.assertIn("Haryana Land Revenue (Amendment) Act, 2025",titles)
    def test_haryana_filter(self):
        rows=search_materials(self.conn,"","All","Haryana")
        self.assertTrue(rows)
        self.assertTrue(all(r["jurisdiction"]=="Haryana" for r in rows))
    def test_seed_is_idempotent(self):
        before=self.conn.execute("SELECT COUNT(*) FROM revenue_law_materials").fetchone()[0]
        seed_revenue_law_catalog(self.conn)
        after=self.conn.execute("SELECT COUNT(*) FROM revenue_law_materials").fetchone()[0]
        self.assertEqual(before,after)

if __name__=="__main__": unittest.main()
