import logging
from logging.handlers import RotatingFileHandler
from app.core.paths import data_dir

def configure_logging() -> None:
    log_path = data_dir() / "logs" / "application.log"
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[handler, logging.StreamHandler()],
        force=True,
    )
