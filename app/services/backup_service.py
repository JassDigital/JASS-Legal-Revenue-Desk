from pathlib import Path
import sqlite3
from datetime import datetime

class BackupService:
    @staticmethod
    def backup(conn, destination):
        destination=Path(destination); destination.parent.mkdir(parents=True,exist_ok=True)
        target=sqlite3.connect(destination)
        try:
            conn.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise ValueError("Backup integrity check failed.")
        finally: target.close()
        return destination

    @staticmethod
    def restore(source, active_database):
        source,active_database=Path(source),Path(active_database)
        if not source.is_file(): raise FileNotFoundError(source)
        check=sqlite3.connect(source)
        try:
            if check.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise ValueError("Backup integrity check failed.")
            if check.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] is None:
                raise ValueError("Not a recognised JASS database backup.")
        finally: check.close()
        active_database.parent.mkdir(parents=True,exist_ok=True)
        src,dst=sqlite3.connect(source),sqlite3.connect(active_database)
        try: src.backup(dst)
        finally: dst.close(); src.close()
        return active_database

def create_backup(database_path, backup_directory):
    database_path=Path(database_path); backup_directory=Path(backup_directory)
    backup_directory.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    target=backup_directory/f"jass-legal-backup-{stamp}.db"
    source=sqlite3.connect(database_path)
    try: return BackupService.backup(source,target)
    finally: source.close()

def restore_backup(backup_path, destination_path):
    return BackupService.restore(backup_path,destination_path)
