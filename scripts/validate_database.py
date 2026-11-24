from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.bootstrap import initialize_database

if __name__ == "__main__":
    conn = initialize_database()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fts = conn.execute("SELECT count(*) FROM legislation_fts").fetchone()[0]
    print("SQLite integrity:", integrity)
    print("FTS5 available: yes")
    print("Indexed legislation rows:", fts)
    conn.close()
    if integrity != "ok":
        raise SystemExit(1)
