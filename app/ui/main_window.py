from PySide6.QtWidgets import QMainWindow,QWidget,QHBoxLayout,QListWidget,QListWidgetItem,QStackedWidget,QLabel,QVBoxLayout
from app.ui.dashboard_page import DashboardPage
from app.ui.search_page import SearchPage
from app.ui.data_pages import LegislationPage,JudgmentsPage,DocumentsPage
from app.ui.judgment_research_page import JudgmentResearchPage
from app.ui.online_sources_page import OnlineSourcesPage
from app.ui.revenue_law_page import RevenueLawPage
from app.ui.revenue_research_page import RevenueResearchPage
from app.ui.revenue_cases_page import RevenueCasesPage
from app.ui.revenue_drafting_page import RevenueDraftingPage
from app.ui.revenue_records_page import RevenueRecordsPage
from app.ui.partition_analysis_page import PartitionAnalysisPage
from app.ui.procedure_assistant_page import ProcedureAssistantPage
from app.ui.legal_source_verification_page import LegalSourceVerificationPage
from app.ui.legal_research_intelligence_page import LegalResearchIntelligencePage
from app.ui.revenue_case_intelligence_page import RevenueCaseIntelligencePage
from app.ui.revenue_document_intelligence_page import RevenueDocumentIntelligencePage
from app.ui.ownership_evidence_workspace_page import OwnershipEvidenceWorkspacePage

class MainWindow(QMainWindow):
    def __init__(self,conn):
        super().__init__(); self.conn=conn
        self.setWindowTitle("JASS Legal & Revenue Desk — V0.1 A17"); self.resize(1380,850)
        root=QWidget(); self.setCentralWidget(root); layout=QHBoxLayout(root)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        self.sidebar=QListWidget(); self.sidebar.setFixedWidth(235); self.sidebar.setObjectName("sidebar")
        names=["Dashboard","Global Search","Legislation","Judgments","Judgment Research","Documents","Official Online Sources","Haryana Revenue Law Library","Haryana Revenue Research Workspace","My Revenue Cases","Case Drafting Studio","Revenue Records Intelligence","Partition & Ownership Analysis","Procedure Assistant","Legal Source Verification","Legal Research Intelligence","Revenue Case Intelligence Dashboard","Legal Document Intelligence","Ownership Evidence Workspace","Research Notes","Settings"]
        for n in names:self.sidebar.addItem(QListWidgetItem(n))
        layout.addWidget(self.sidebar); self.stack=QStackedWidget(); layout.addWidget(self.stack,1)
        self.stack.addWidget(DashboardPage(conn)); self.stack.addWidget(SearchPage(conn))
        self.stack.addWidget(LegislationPage(conn)); self.stack.addWidget(JudgmentsPage(conn))
        self.stack.addWidget(JudgmentResearchPage(conn)); self.stack.addWidget(DocumentsPage(conn)); self.stack.addWidget(OnlineSourcesPage(conn)); self.stack.addWidget(RevenueLawPage(conn)); self.stack.addWidget(RevenueResearchPage(conn)); self.stack.addWidget(RevenueCasesPage(conn)); self.stack.addWidget(RevenueDraftingPage(conn)); self.stack.addWidget(RevenueRecordsPage(conn)); self.stack.addWidget(PartitionAnalysisPage(conn)); self.stack.addWidget(ProcedureAssistantPage(conn)); self.stack.addWidget(LegalSourceVerificationPage(conn)); self.stack.addWidget(LegalResearchIntelligencePage(conn)); self.stack.addWidget(RevenueCaseIntelligencePage(conn)); self.stack.addWidget(RevenueDocumentIntelligencePage(conn)); self.stack.addWidget(OwnershipEvidenceWorkspacePage(conn))
        for n in ["Research Notes","Settings"]:
            page=QWidget(); pl=QVBoxLayout(page); h=QLabel(n); h.setObjectName("pageTitle"); pl.addWidget(h)
            msg=QLabel("This module is planned for a later milestone."); msg.setObjectName("muted"); pl.addWidget(msg); pl.addStretch(1); self.stack.addWidget(page)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex); self.sidebar.setCurrentRow(0)
        self.statusBar().showMessage("Offline mode — local database")
        self.setStyleSheet("""
        QMainWindow{background:#f3f5f8} #sidebar{background:#172638;color:#edf2f7;border:0;padding:12px 6px}
        #sidebar::item{padding:13px 12px;margin:3px 2px;border-radius:6px} #sidebar::item:selected{background:#30465e;color:white}
        QLabel#pageTitle{font-size:25px;font-weight:650;color:#1b2b3b;padding:4px 0} QLabel#muted{color:#657487;font-size:13px}
        QLabel#metricValue{font-size:30px;font-weight:700;color:#243b53} QFrame#metricCard{background:white;border:1px solid #dce3eb;border-radius:10px}
        QLabel#notice{background:#fff7e6;color:#76551a;border:1px solid #f0d89e;padding:12px;border-radius:7px}
        QPushButton{background:#244a70;color:white;padding:9px 18px;border-radius:5px} QPushButton:hover{background:#315f8d}
        QLineEdit{padding:10px;border:1px solid #cbd5e1;border-radius:5px;background:white}
        QTableWidget{background:white;border:1px solid #dce3eb} QComboBox{padding:7px;min-width:120px}
        """)
    def closeEvent(self,event):
        try:self.conn.close()
        except Exception:pass
        event.accept()
