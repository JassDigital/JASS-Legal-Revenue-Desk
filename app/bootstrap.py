import logging
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from app.core.logging_config import configure_logging
from app.database.bootstrap import initialize_database
from app.services.sample_data import load_sample_data
from app.services.revenue_law_catalog import seed_revenue_law_catalog
from app.services.revenue_research_workspace import seed_topics
from app.ui.main_window import MainWindow

def run() -> int:
    configure_logging()
    logger = logging.getLogger(__name__)
    app = QApplication(sys.argv)
    app.setApplicationName("JASS Legal & Revenue Desk")
    try:
        conn = initialize_database()
        load_sample_data(conn)
        seed_revenue_law_catalog(conn)
        seed_topics(conn)
        window = MainWindow(conn)
        window.show()
        return app.exec()
    except Exception as exc:
        logger.exception("Application startup failed")
        QMessageBox.critical(
            None, "Startup error",
            f"The application could not start:\n\n{exc}\n\nSee the application log for details."
        )
        return 1
