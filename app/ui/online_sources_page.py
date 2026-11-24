from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,
    QTableWidget,QTableWidgetItem,QHeaderView,QMessageBox,QDialog,QFormLayout,QDialogButtonBox,
    QComboBox,QTextEdit)
from app.services.online_source_service import OnlineSourceService, OnlineImportError, OFFICIAL_SOURCES

class OnlineImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from an official legal source")
        layout=QVBoxLayout(self); form=QFormLayout()
        self.url=QLineEdit(); self.url.setPlaceholderText("Paste the direct HTTPS PDF or TXT URL")
        self.title=QLineEdit()
        self.kind=QComboBox(); self.kind.addItems(["Acts","Judgments","Gazette","Orders","Other"])
        form.addRow("Direct document URL",self.url); form.addRow("Document title (optional)",self.title); form.addRow("Document category",self.kind)
        layout.addLayout(form)
        info=QLabel("Allowed hosts: " + ", ".join(x["host"] for x in OFFICIAL_SOURCES.values()) +
            "\\nOnly direct PDF or plain-text downloads are accepted. Maximum 40 MB. Redirects to other hosts are blocked.")
        info.setWordWrap(True); layout.addWidget(info)
        note=QLabel("An official host does not prove that a document is current, complete, authentic or legally operative. Review every import before relying on it.")
        note.setWordWrap(True); note.setObjectName("notice"); layout.addWidget(note)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); buttons.button(QDialogButtonBox.Ok).setText("Download and import")
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)

class OnlineSourcesPage(QWidget):
    def __init__(self, conn):
        super().__init__(); self.conn=conn; self.service=OnlineSourceService(conn)
        layout=QVBoxLayout(self)
        heading=QLabel("Official Online Sources"); heading.setObjectName("pageTitle"); layout.addWidget(heading)
        desc=QLabel("User-initiated imports from a limited allowlist of official publisher hosts. No background scraping or silent replacement.")
        desc.setWordWrap(True); desc.setObjectName("muted"); layout.addWidget(desc)
        row=QHBoxLayout()
        btn=QPushButton("Import from official URL"); btn.clicked.connect(self.import_url); row.addWidget(btn)
        refresh=QPushButton("Refresh history"); refresh.clicked.connect(self.refresh); row.addWidget(refresh); row.addStretch(1)
        layout.addLayout(row)
        self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(["ID","Document","Source","Imported","SHA-256","Result"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table,1); self.refresh()
    def refresh(self):
        rows=self.conn.execute("""SELECT l.online_import_id,d.document_title,s.source_name,l.fetched_at,l.sha256,l.result
            FROM online_import_log l LEFT JOIN documents d ON d.document_id=l.document_id
            LEFT JOIN sources s ON s.source_id=l.source_id ORDER BY l.online_import_id DESC""").fetchall()
        self.table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,val in enumerate(row): self.table.setItem(i,j,QTableWidgetItem("" if val is None else str(val)))
    def import_url(self):
        dialog=OnlineImportDialog(self)
        if not dialog.exec(): return
        if not dialog.url.text().strip():
            QMessageBox.warning(self,"URL required","Enter a direct HTTPS document URL."); return
        confirm=QMessageBox.question(self,"Confirm download","Download this document now? The request will contact the supplied official host.")
        if confirm != QMessageBox.Yes: return
        try:
            doc_id=self.service.fetch_and_import(dialog.url.text(),dialog.title.text(),dialog.kind.currentText())
            QMessageBox.information(self,"Import complete",f"Imported as document #{doc_id}. Review its source and legal status before relying on it.")
            self.refresh()
        except OnlineImportError as exc: QMessageBox.warning(self,"Import not completed",str(exc))
        except Exception as exc: QMessageBox.critical(self,"Import error",str(exc))
