import tempfile, unittest
from pathlib import Path
from app.database.connection import connect
from app.database.migrations import migrate
from app.database.repositories import JudgmentRepository
from app.services.judgment_research_service import JudgmentResearchService

class JudgmentResearchTests(unittest.TestCase):
    def test_search_facets_topics_and_references(self):
        with tempfile.TemporaryDirectory() as td:
            conn=connect(Path(td)/"db.sqlite"); migrate(conn)
            repo=JudgmentRepository(conn)
            one=repo.create("A v State","CWP-1","2024 P&H 100","2024-03-10",
                "Justice Example","https://example.invalid/judgment",
                "The Court considered mutation entries and co-sharer partition.",
                "unverified","Punjab and Haryana High Court","A","State of Haryana",
                "mutation partition co-sharer")
            two=repo.create("B v State","RSA-2","2022 SC 20","2022-01-01",
                "Justice Sample","","Inheritance and title dispute.","unverified",
                "Supreme Court of India","B","State","inheritance title")
            service=JudgmentResearchService(conn)
            service.add_topic(one,"Mutation")
            service.add_statutory_reference(one,"Punjab Land Revenue Act, 1887","44","Record presumption")
            service.add_relation(one,two,"Referred","Manual researcher note")
            self.assertEqual(len(service.search("co-sharer")),1)
            self.assertEqual(len(service.search("",court="Supreme Court of India")),1)
            self.assertEqual(len(service.search("",topic="mutation")),1)
            self.assertEqual(service.statutory_references(one)[0]["section_number"],"44")
            self.assertEqual(service.related(one)[0]["target_judgment_id"],two)
            conn.close()

if __name__=="__main__":unittest.main()
