import tempfile, unittest, sqlite3
from pathlib import Path
from app.database.connection import connect
from app.database.migrations import migrate
from app.services.backup_service import create_backup, restore_backup

class BackupCompatibilityTests(unittest.TestCase):
    def test_legacy_backup_api(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); db=base/"source.db"
            conn=connect(db); migrate(conn)
            conn.execute("INSERT INTO research_notes(title,content) VALUES('Backup test','Preserve me')")
            conn.commit(); conn.close()
            backup=create_backup(db,base/"backups")
            restored=base/"restored.db"
            restore_backup(backup,restored)
            check=sqlite3.connect(restored)
            self.assertEqual(check.execute("SELECT content FROM research_notes WHERE title='Backup test'").fetchone()[0],"Preserve me")
            check.close()

if __name__=="__main__":unittest.main()
