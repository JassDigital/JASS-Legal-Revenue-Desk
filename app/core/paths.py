from pathlib import Path
import os
import sys

APP_NAME = "JASS-Legal-Revenue-Desk"

def data_dir() -> Path:
    """Return a per-user writable data directory on Linux or Windows."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    for name in ("database", "documents", "backups", "logs", "exports"):
        (path / name).mkdir(exist_ok=True)
    return path

def database_path() -> Path:
    return data_dir() / "database" / "jass_legal_revenue.db"
