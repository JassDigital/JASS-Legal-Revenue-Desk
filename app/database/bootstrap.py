from app.database.connection import connect
from app.database.migrations import migrate
from app.core.paths import database_path

def initialize_database():
    conn = connect(database_path())
    try:
        migrate(conn)
        # FTS5 is required for the initial search foundation.
        conn.execute("SELECT count(*) FROM legislation_fts").fetchone()
        return conn
    except Exception:
        conn.close()
        raise
