import tempfile, unittest
from pathlib import Path
from app.database.connection import connect
from app.database.migrations import migrate
from app.database.repositories import LegislationRepository, JudgmentRepository
from app.services.backup_service import BackupService

class A2Tests(unittest.TestCase):
    def test_repositories_and_fts(self):
        with tempfile.TemporaryDirectory() as td:
            conn=connect(Path(td)/"db.sqlite"); migrate(conn)
            repo=LegislationRepository(conn)
            lid=repo.create("Test Haryana Revenue Act","Test HRA","7",2025,"Haryana")
            conn.execute("INSERT INTO sections(legislation_id,section_number,section_title,section_text) VALUES(?,?,?,?)",
                         (lid,"44","Presumption","Revenue record entries"))
            conn.commit()
            JudgmentRepository(conn).create("Sample v State",citation="2025 Demo 1",full_text="Mutation and land revenue")
            self.assertEqual(len(repo.list("Revenue")),1)
            self.assertTrue(conn.execute("SELECT rowid FROM sections_fts WHERE sections_fts MATCH 'Presumption'").fetchone())
            conn.close()
    def test_backup(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"db.sqlite"; backup=Path(td)/"backup.sqlite"
            conn=connect(db); migrate(conn); conn.execute("INSERT INTO sources(source_name,source_type) VALUES('x','test')"); conn.commit()
            BackupService.backup(conn,backup); conn.close()
            check=connect(backup); self.assertEqual(check.execute("SELECT COUNT(*) FROM sources").fetchone()[0],1); check.close()

if __name__=="__main__":unittest.main()
