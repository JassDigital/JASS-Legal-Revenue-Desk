from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,
    QTableWidget,QTableWidgetItem,QHeaderView,QMessageBox,QDialog,QFormLayout,QDialogButtonBox,
    QComboBox,QTextEdit)
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from app.services.revenue_law_catalog import search_materials

class MaterialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Add legal material")
        layout=QVBoxLayout(self); form=QFormLayout(); self.widgets={}
        fields=[
            ("title","Title",False),("material_type","Material type",False),("jurisdiction","Jurisdiction",False),
            ("year","Year",False),("act_number","Act / notification number",False),
            ("publication_date","Publication date YYYY-MM-DD",False),("effective_date","Effective date YYYY-MM-DD",False),
            ("subject_tags","Subject tags (separate with semicolons)",False),("source_name","Source / publisher",False),
            ("source_url","Source URL",False),("source_classification","Source classification",False),
            ("legal_status","Legal status / review state",False),("description","Description",True),
            ("verification_notes","Verification notes",True)]
        for key,label,multi in fields:
            w=QTextEdit() if multi else QLineEdit()
            if multi: w.setMinimumHeight(70)
            self.widgets[key]=w; form.addRow(label,w)
        self.widgets["material_type"].setText("Other")
        self.widgets["jurisdiction"].setText("Haryana")
        self.widgets["source_classification"].setText("needs_source_review")
        self.widgets["legal_status"].setText("needs_legal_verification")
        layout.addLayout(form)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
    def values(self):
        result={}
        for k,w in self.widgets.items():
            result[k]=w.toPlainText().strip() if isinstance(w,QTextEdit) else w.text().strip()
        result["year"]=int(result["year"]) if result["year"] else None
        return result

class RevenueLawPage(QWidget):
    def __init__(self, conn):
        super().__init__(); self.conn=conn
        layout=QVBoxLayout(self)
        title=QLabel("Haryana Revenue Law Library"); title.setObjectName("pageTitle"); layout.addWidget(title)
        intro=QLabel("A curated register of Acts, amendments, rules, Gazette notifications and land-record instructions. Review states are explicit; inclusion does not certify current legal validity.")
        intro.setWordWrap(True); intro.setObjectName("muted"); layout.addWidget(intro)
        row=QHBoxLayout(); self.query=QLineEdit(); self.query.setPlaceholderText("Search mutation, partition, Jamabandi, Act number, subject...")
        self.query.returnPressed.connect(self.refresh); row.addWidget(self.query,1)
        self.kind=QComboBox(); self.kind.addItems(["All","Principal Act","Amending Act","State Act","Rules","Manual / Gazette Notification","Gazette Notification","Circular / Instruction","Judgment"]); self.kind.currentTextChanged.connect(self.refresh); row.addWidget(self.kind)
        self.jurisdiction=QComboBox(); self.jurisdiction.addItems(["All","Haryana","Central","Punjab"]); self.jurisdiction.currentTextChanged.connect(self.refresh); row.addWidget(self.jurisdiction)
        add=QPushButton("Add material"); add.clicked.connect(self.add_material); row.addWidget(add)
        refresh=QPushButton("Refresh"); refresh.clicked.connect(self.refresh); row.addWidget(refresh)
        layout.addLayout(row)
        self.table=QTableWidget(0,7); self.table.setHorizontalHeaderLabels(["ID","Title","Type","Year","Act / Notification","Legal review state","Source classification"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self.open_source)
        layout.addWidget(self.table,1)
        self.detail=QTextEdit(); self.detail.setReadOnly(True); self.detail.setMaximumHeight(150); self.detail.setPlaceholderText("Select a material to view description and verification notes. Double-click a row to open its source.")
        self.table.itemSelectionChanged.connect(self.show_detail); layout.addWidget(self.detail)
        self.refresh()
    def refresh(self):
        rows=search_materials(self.conn,self.query.text(),self.kind.currentText(),self.jurisdiction.currentText())
        self.rows=rows; self.table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            values=[r["material_id"],r["title"],r["material_type"],r["year"],r["act_number"],r["legal_status"],r["source_classification"]]
            for j,v in enumerate(values):
                item=QTableWidgetItem("" if v is None else str(v)); self.table.setItem(i,j,item)
        self.detail.clear()
    def show_detail(self):
        row=self.table.currentRow()
        if row<0 or row>=len(self.rows): return
        r=self.rows[row]
        self.detail.setPlainText(
            f"Description: {r['description']}\n\nSource: {r['source_name']}\nURL: {r['source_url']}\n\n"
            f"Publication date: {r['publication_date']} | Effective date: {r['effective_date']}\n"
            f"Subjects: {r['subject_tags']}\n\nVerification notes: {r['verification_notes']}")
    def open_source(self,row,column):
        if row<len(self.rows):
            url=self.rows[row]["source_url"]
            if url: QDesktopServices.openUrl(QUrl(url))
            else: QMessageBox.information(self,"No source URL","No source URL has been recorded for this material.")
    def add_material(self):
        dialog=MaterialDialog(self)
        if not dialog.exec(): return
        try:
            v=dialog.values()
            if not v["title"]: raise ValueError("Title is required.")
            keys=list(v.keys())
            self.conn.execute("INSERT INTO revenue_law_materials("+",".join(keys)+") VALUES("+",".join("?" for _ in keys)+")",[v[k] for k in keys])
            self.conn.commit(); self.refresh()
        except Exception as exc: QMessageBox.warning(self,"Could not save",str(exc))
