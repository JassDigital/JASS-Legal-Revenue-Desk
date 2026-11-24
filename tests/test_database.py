import tempfile
import unittest
from pathlib import Path
from app.database.connection import connect
from app.database.migrations import migrate
from app.services.sample_data import load_sample_data
from app.services.search_service import SearchService

class DatabaseTests(unittest.TestCase):
    def test_migration_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect(Path(tmp) / "test.db")
            migrate(conn)
            load_sample_data(conn)
            results = SearchService(conn).search("demonstration")
            self.assertTrue(results)
            self.assertTrue(any(r["kind"] == "Judgment" for r in results))
            conn.close()

if __name__ == "__main__":
    unittest.main()

class BackupTests(unittest.TestCase):
    def test_backup_and_restore(self):
        import sqlite3
        from app.services.backup_service import create_backup, restore_backup
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            db = base / 'source.db'
            conn = connect(db)
            migrate(conn)
            conn.execute("INSERT INTO research_notes(title,content) VALUES('Backup test','Preserve me')")
            conn.commit()
            conn.close()
            backup = create_backup(db, base / 'backups')
            restored = base / 'restored.db'
            restore_backup(backup, restored)
            check = sqlite3.connect(restored)
            try:
                value = check.execute("SELECT content FROM research_notes WHERE title='Backup test'").fetchone()[0]
                self.assertEqual(value, 'Preserve me')
            finally:
                check.close()
