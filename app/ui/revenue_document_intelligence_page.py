from pathlib import Path
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QLineEdit,
 QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView,QTabWidget,QDialog,QFormLayout,QDialogButtonBox,
 QTextEdit,QMessageBox,QFileDialog)
from app.services.revenue_case_service import list_cases
from app.services.revenue_document_intelligence import (search_documents,document_detail,save_document_metadata,
 case_link_options,add_case_document_link,list_case_document_links,delete_case_document_link,build_case_evidence_index,LINK_TYPES,VERIFY_STATES)

class MetadataDialog(QDialog):
    fields=[("record_date","Record date (YYYY-MM-DD)"),("issuing_authority","Issuing authority / office"),
      ("record_reference","Record number / reference"),("village","Village"),("tehsil","Tehsil"),
      ("district","District"),("khasra_numbers","Khasra number(s)"),("khata_number","Khata / Khatauni"),
      ("jamabandi_year","Jamabandi year"),("metadata_status","Metadata verification")]
    def __init__(self,row,parent=None):
        super().__init__(parent);self.setWindowTitle("Revenue document metadata");layout=QVBoxLayout(self);form=QFormLayout();self.widgets={}
        for key,label in self.fields:
            if key=="metadata_status":
                w=QComboBox();w.addItems(VERIFY_STATES)
            else:w=QLineEdit()
            value=row[key] if row and key in row.keys() else ""
            if value is not None:
                if isinstance(w,QComboBox):w.setCurrentText(str(value))
                else:w.setText(str(value))
            self.widgets[key]=w;form.addRow(label,w)
        self.notes=QTextEdit();self.notes.setMinimumHeight(90)
        if row and "page_notes" in row.keys():self.notes.setPlainText(row["page_notes"] or "")
        form.addRow("Page / metadata notes",self.notes);layout.addLayout(form)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def values(self):
        v={k:(w.currentText() if isinstance(w,QComboBox) else w.text().strip()) for k,w in self.widgets.items()}
        v["page_notes"]=self.notes.toPlainText().strip();return v

class LinkDialog(QDialog):
    def __init__(self,conn,case_id,parent=None):
        super().__init__(parent);self.setWindowTitle("Link document to revenue case");docs,parties,issues=case_link_options(conn,case_id)
        layout=QVBoxLayout(self);form=QFormLayout();self.doc=QComboBox()
        for r in docs:self.doc.addItem(f"#{r['document_id']} — {r['document_title']} [{r['document_type']}]",r["document_id"])
        self.party=QComboBox();self.party.addItem("No party link",None)
        for r in parties:self.party.addItem(f"{r['party_name']} — {r['role']}",r["party_id"])
        self.issue=QComboBox();self.issue.addItem("No issue link",None)
        for r in issues:self.issue.addItem(r["issue_title"],r["issue_id"])
        self.kind=QComboBox();self.kind.addItems(LINK_TYPES)
        self.pages=QLineEdit();self.pages.setPlaceholderText("e.g. pages 2–4 or paragraph 12")
        self.relevance=QLineEdit();self.relevance.setPlaceholderText("Why this document matters to the case")
        self.verify=QComboBox();self.verify.addItems(VERIFY_STATES)
        self.notes=QLineEdit()
        for label,w in [("Document",self.doc),("Related party",self.party),("Related legal issue",self.issue),("Link type",self.kind),("Page / paragraph reference",self.pages),("Relevance",self.relevance),("Verification status",self.verify),("Notes",self.notes)]:form.addRow(label,w)
        layout.addLayout(form);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def values(self):
        return self.doc.currentData(),{"party_id":self.party.currentData(),"issue_id":self.issue.currentData(),"link_type":self.kind.currentText(),"page_reference":self.pages.text().strip(),"relevance_note":self.relevance.text().strip(),"verification_status":self.verify.currentText(),"notes":self.notes.text().strip()}

class RevenueDocumentIntelligencePage(QWidget):
    def __init__(self,conn):
        super().__init__();self.conn=conn
        root=QVBoxLayout(self);title=QLabel("Legal Document Intelligence & Evidence Analysis");title.setObjectName("pageTitle");root.addWidget(title)
        note=QLabel("Search extracted PDF/TXT text, record revenue-document metadata, and link existing library documents to cases, parties and legal issues. Original files are not modified.")
        note.setWordWrap(True);note.setObjectName("muted");root.addWidget(note)
        row=QHBoxLayout();row.addWidget(QLabel("Case context"));self.case=QComboBox();self.case.currentIndexChanged.connect(self.refresh_links);row.addWidget(self.case,2)
        self.query=QLineEdit();self.query.setPlaceholderText("Search document title, record number, Khasra or extracted text…");self.query.returnPressed.connect(self.refresh_documents);row.addWidget(self.query,3)
        self.type=QComboBox();self.type.addItems(["All","Acts","Judgments","Revenue Record","Orders","Other"]);self.type.currentIndexChanged.connect(self.refresh_documents);row.addWidget(self.type)
        b=QPushButton("Search");b.clicked.connect(self.refresh_documents);row.addWidget(b);root.addLayout(row)
        buttons=QHBoxLayout()
        for label,fn in [("Refresh library",self.refresh_documents),("Edit metadata",self.edit_metadata),("Link to case",self.add_link),("Remove selected link",self.remove_link),("Export case evidence index",self.export_index)]:
            b=QPushButton(label);b.clicked.connect(fn);buttons.addWidget(b)
        root.addLayout(buttons)
        self.tabs=QTabWidget();root.addWidget(self.tabs,1)
        page=QWidget();lay=QVBoxLayout(page);self.docs=self._table(["ID","Title","Type","Filename","Pages","Extraction","Record ref","Village","Khasra","Text match excerpt"]);self.docs.currentCellChanged.connect(lambda *_:self.show_selected_text());lay.addWidget(self.docs);self.tabs.addTab(page,"Document Search")
        page=QWidget();lay=QVBoxLayout(page);self.links=self._table(["Link ID","Document","Type","Party","Issue","Page ref","Relevance","Verification"]);lay.addWidget(self.links);self.tabs.addTab(page,"Case Evidence Links")
        page=QWidget();lay=QVBoxLayout(page);self.preview=QTextEdit();self.preview.setReadOnly(True);self.preview.setPlaceholderText("Select a document in Document Search to inspect its extracted text.");lay.addWidget(self.preview);self.tabs.addTab(page,"Extracted Text")
        self.load_cases()
    def _table(self,headers):
        t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);t.horizontalHeader().setStretchLastSection(True);t.setSelectionBehavior(QAbstractItemView.SelectRows);t.setEditTriggers(QAbstractItemView.NoEditTriggers);t.setAlternatingRowColors(True);return t
    def load_cases(self):
        old=self.case.currentData();self.case.blockSignals(True);self.case.clear()
        for r in list_cases(self.conn):self.case.addItem(f"#{r['case_id']} — {r['case_title']}",r["case_id"])
        idx=self.case.findData(old)
        if idx>=0:self.case.setCurrentIndex(idx)
        self.case.blockSignals(False);self.refresh_documents();self.refresh_links()
    def selected_id(self,table):
        row=table.currentRow()
        if row<0 or table.item(row,0) is None:return None
        return int(table.item(row,0).text())
    def refresh_documents(self):
        rows=search_documents(self.conn,self.query.text(),self.type.currentText())
        self.docs.setRowCount(len(rows))
        for i,r in enumerate(rows):
            vals=[r["document_id"],r["document_title"],r["document_type"],r["original_filename"],r["page_count"],r["extraction_status"],r["record_reference"],r["village"],r["khasra_numbers"],r["excerpt"]]
            for j,v in enumerate(vals):self.docs.setItem(i,j,QTableWidgetItem("" if v is None else str(v)))
        if rows:self.docs.selectRow(0);self.show_selected_text()
        else:self.preview.clear()
    def refresh_links(self,*args):
        cid=self.case.currentData()
        if cid is None:self.links.setRowCount(0);return
        rows=list_case_document_links(self.conn,cid);self.links.setRowCount(len(rows))
        for i,r in enumerate(rows):
            vals=[r["link_id"],r["document_title"],r["link_type"],r["party_name"],r["issue_title"],r["page_reference"],r["relevance_note"],r["verification_status"]]
            for j,v in enumerate(vals):self.links.setItem(i,j,QTableWidgetItem("" if v is None else str(v)))
    def show_selected_text(self):
        did=self.selected_id(self.docs)
        if did is None:self.preview.clear();return
        row=document_detail(self.conn,did)
        self.preview.setPlainText((row["extracted_text"] or "") if row else "")
    def edit_metadata(self):
        did=self.selected_id(self.docs)
        if did is None:QMessageBox.information(self,"Select document","Select a document first.");return
        d=MetadataDialog(document_detail(self.conn,did),self)
        if d.exec():
            try:save_document_metadata(self.conn,did,d.values());self.refresh_documents()
            except Exception as e:QMessageBox.warning(self,"Metadata save failed",str(e))
    def add_link(self):
        cid=self.case.currentData()
        if cid is None:QMessageBox.information(self,"Select case","Create or select a case first.");return
        if not self.docs.rowCount():QMessageBox.information(self,"No documents","Import documents in the Document Library first.");return
        d=LinkDialog(self.conn,cid,self)
        if d.exec():
            did,v=d.values()
            try:add_case_document_link(self.conn,cid,did,v);self.refresh_links();self.tabs.setCurrentIndex(1)
            except Exception as e:QMessageBox.warning(self,"Could not link document",str(e))
    def remove_link(self):
        lid=self.selected_id(self.links)
        if lid is None:return
        if QMessageBox.question(self,"Remove link","Remove this case-document link? The original library document will remain.")==QMessageBox.Yes:
            delete_case_document_link(self.conn,lid);self.refresh_links()
    def export_index(self):
        cid=self.case.currentData()
        if cid is None:QMessageBox.information(self,"Select case","Select a case first.");return
        path,_=QFileDialog.getSaveFileName(self,"Export case evidence index",f"case-{cid}-evidence-index.txt","Text files (*.txt)")
        if path:
            try:
                Path(path).write_text(build_case_evidence_index(self.conn,cid),encoding="utf-8")
                QMessageBox.information(self,"Exported",f"Saved evidence index to:\\n{path}")
            except Exception as e:QMessageBox.warning(self,"Export failed",str(e))
