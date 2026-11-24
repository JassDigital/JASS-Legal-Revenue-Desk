import sqlite3
import unittest
from app.database.migrations import migrate
from app.services.revenue_law_catalog import seed_revenue_law_catalog
from app.services.revenue_research_workspace import (seed_topics,materials,sections,save_section,
    annotations,save_annotation,amendments,save_amendment,topic_rows,link_topic_material,topic_materials,
    material_links,save_material_link)

class A6ResearchWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(":memory:")
        self.conn.row_factory=sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        migrate(self.conn); seed_revenue_law_catalog(self.conn); seed_topics(self.conn)
        self.material_id=materials(self.conn)[0]["material_id"]
    def tearDown(self): self.conn.close()
    def test_schema_v6(self):
        self.assertGreaterEqual(self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],6)
    def test_section_reader_and_annotation(self):
        save_section(self.conn,self.material_id,"111A","Partition","User-entered verified-source transcription","Gazette p. 4","2025-04-16","","checked")
        row=sections(self.conn,self.material_id)[0]
        self.assertEqual(row["section_number"],"111A")
        self.assertEqual(len(sections(self.conn,self.material_id,"Partition")),1)
        self.assertEqual(len(sections(self.conn,self.material_id,"not-present")),0)
        save_annotation(self.conn,self.material_id,row["section_id"],"Case note","Research point","Compare notification applicability","partition")
        self.assertEqual(annotations(self.conn,self.material_id)[0]["title"],"Research point")
    def test_amendment_timeline(self):
        save_amendment(self.conn,self.material_id,"111A","Haryana Land Revenue Amendment Act, 2025",None,"2025-04-16","","Amended provision","Gazette 16-04-2025","unverified")
        self.assertEqual(amendments(self.conn,self.material_id)[0]["affected_section"],"111A")
    def test_topic_and_material_relationship(self):
        topic=topic_rows(self.conn)[0]
        link_topic_material(self.conn,topic["topic_id"],self.material_id,"Relevant")
        self.assertEqual(len(topic_materials(self.conn,topic["topic_id"])),1)
        other=[m for m in materials(self.conn) if m["material_id"]!=self.material_id][0]
        save_material_link(self.conn,self.material_id,other["material_id"],"Related","Cross reference","unverified")
        self.assertEqual(material_links(self.conn,self.material_id)[0]["target_title"],other["title"])

if __name__=="__main__":unittest.main()
