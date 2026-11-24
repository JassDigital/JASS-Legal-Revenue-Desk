from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,
    QTableWidget,QTableWidgetItem,QHeaderView,QComboBox,QFileDialog,QMessageBox,QFormLayout,
    QDialog,QDialogButtonBox,QTextEdit)
from app.database.repositories import LegislationRepository,JudgmentRepository,DocumentRepository
from app.services.document_import_service import DocumentImportService

class EntryDialog(QDialog):
    def __init__(self,title,fields,parent=None):
        super().__init__(parent); self.setWindowTitle(title); self.widgets={}
        layout=QVBoxLayout(self); form=QFormLayout()
        for key,label,multi in fields:
            w=QTextEdit() if multi else QLineEdit()
            if multi: w.setMinimumHeight(120)
            self.widgets[key]=w; form.addRow(label,w)
        layout.addLayout(form)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
    def values(self):
        return {k:(w.toPlainText().strip() if isinstance(w,QTextEdit) else w.text().strip())
                for k,w in self.widgets.items()}

class BaseTablePage(QWidget):
    headers=[]
    def __init__(self):
        super().__init__(); layout=QVBoxLayout(self)
        self.heading=QLabel(); self.heading.setObjectName("pageTitle"); layout.addWidget(self.heading)
        row=QHBoxLayout(); self.query=QLineEdit(); self.query.setPlaceholderText("Filter records...")
        self.query.returnPressed.connect(self.refresh); row.addWidget(self.query,1)
        self.filter=QComboBox(); self.filter.addItem("All"); row.addWidget(self.filter)
        btn=QPushButton("Refresh"); btn.clicked.connect(self.refresh); row.addWidget(btn); layout.addLayout(row)
        self.table=QTableWidget(0,len(self.headers)); self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table,1)
    def fill(self,rows):
        self.table.setRowCount(len(rows))
        for r,values in enumerate(rows):
            for c,value in enumerate(values): self.table.setItem(r,c,QTableWidgetItem("" if value is None else str(value)))

class LegislationPage(BaseTablePage):
    headers=["ID","Title","Short title","Year","Jurisdiction","Status"]
    def __init__(self,conn):
        super().__init__(); self.repo=LegislationRepository(conn); self.heading.setText("Legislation Library")
        self.filter.addItems(["Haryana","Central","Other"])
        add=QPushButton("Add legislation metadata"); add.clicked.connect(self.add_record)
        self.layout().insertWidget(2,add); self.refresh()
    def refresh(self):
        rows=self.repo.list(self.query.text(),self.filter.currentText())
        self.fill([(r["legislation_id"],r["title"],r["short_title"],r["year"],r["jurisdiction"],r["current_status"]) for r in rows])
    def add_record(self):
        d=EntryDialog("Add legislation metadata",[("title","Full title",False),("short_title","Short title",False),
            ("act_number","Act number",False),("year","Year",False),("jurisdiction","Jurisdiction",False)],self)
        if d.exec():
            v=d.values()
            if not v["title"]: QMessageBox.warning(self,"Required","Full title is required."); return
            try: self.repo.create(v["title"],v["short_title"],v["act_number"],int(v["year"]) if v["year"] else None,v["jurisdiction"] or "Haryana"); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Save failed",str(e))

class JudgmentsPage(BaseTablePage):
    headers=["ID","Case title","Citation","Decision date","Verification"]
    def __init__(self,conn):
        super().__init__(); self.repo=JudgmentRepository(conn); self.heading.setText("Judgment Library")
        self.filter.addItems(["unverified","official_verified","secondary_source","sample_only"])
        add=QPushButton("Add judgment metadata"); add.clicked.connect(self.add_record); self.layout().insertWidget(2,add); self.refresh()
    def refresh(self):
        rows=self.repo.list(self.query.text(),verification=self.filter.currentText())
        self.fill([(r["judgment_id"],r["case_title"],r["citation"],r["decision_date"],r["verification_status"]) for r in rows])
    def add_record(self):
        d=EntryDialog("Add judgment metadata",[("case_title","Case title",False),("case_number","Case number",False),
            ("citation","Citation",False),("decision_date","Decision date YYYY-MM-DD",False),
            ("judge_names","Judge(s)",False),("official_url","Official source URL",False),("full_text","Judgment text",True)],self)
        if d.exec():
            v=d.values()
            if not v["case_title"]: QMessageBox.warning(self,"Required","Case title is required."); return
            try: self.repo.create(v["case_title"],v["case_number"],v["citation"],v["decision_date"],v["judge_names"],v["official_url"],v["full_text"]); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Save failed",str(e))

class DocumentsPage(BaseTablePage):
    headers=["ID","Title","Type","Filename","Imported","Extraction"]
    def __init__(self,conn):
        super().__init__(); self.repo=DocumentRepository(conn); self.importer=DocumentImportService(conn)
        self.heading.setText("Document Library"); self.filter.addItems(["Acts","Judgments","Revenue Record","Orders","Other"])
        add=QPushButton("Import PDF / TXT"); add.clicked.connect(self.import_document); self.layout().insertWidget(2,add); self.refresh()
    def refresh(self):
        rows=self.repo.list(self.query.text(),self.filter.currentText())
        self.fill([(r["document_id"],r["document_title"],r["document_type"],r["original_filename"],r["imported_at"],r["extraction_status"]) for r in rows])
    def import_document(self):
        path,_=QFileDialog.getOpenFileName(self,"Import document","","PDF or text (*.pdf *.txt)")
        if not path:return
        try:
            doc_type=self.filter.currentText()
            if doc_type=="All":doc_type="Other"
            doc_id=self.importer.import_file(path,doc_type)
            QMessageBox.information(self,"Imported",f"Imported as document #{doc_id}.")
            self.refresh()
        except Exception as e:QMessageBox.critical(self,"Import failed",str(e))
