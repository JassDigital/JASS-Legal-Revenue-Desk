from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.bootstrap import initialize_database

if __name__ == "__main__":
    conn = initialize_database()
    print("Database initialized successfully.")
    print("Schema version:", conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0])
    conn.close()
