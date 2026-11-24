from pathlib import Path
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QTableWidget,
    QTableWidgetItem,QHeaderView,QAbstractItemView,QDialog,QFormLayout,QLineEdit,QTextEdit,QDialogButtonBox,
    QMessageBox,QFileDialog)
from app.services.revenue_case_service import list_cases
from app.services.revenue_drafting_service import (DRAFT_TYPES,DRAFT_STATUSES,list_drafts,get_draft,save_draft,
    delete_draft,evidence_link_options,add_evidence_link,list_evidence_links,delete_evidence_link,build_case_report)
from app.services.legal_draft_assembly import eligible_bundles,create_draft_from_bundle,build_draft_export,draft_source_register

class DraftDialog(QDialog):
    def __init__(self,parent=None,row=None):
        super().__init__(parent);self.setWindowTitle("Case document draft");layout=QVBoxLayout(self);form=QFormLayout()
        self.kind=QComboBox();self.kind.addItems(DRAFT_TYPES)
        self.title=QLineEdit();self.status=QComboBox();self.status.addItems(DRAFT_STATUSES)
        self.body=QTextEdit();self.body.setMinimumSize(680,430)
        form.addRow("Document type",self.kind);form.addRow("Title",self.title);form.addRow("Status",self.status)
        layout.addLayout(form);layout.addWidget(QLabel("Draft text — enter and verify all names, facts, sections, dates and prayers."))
        layout.addWidget(self.body,1)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        if row:
            self.kind.setCurrentText(row["draft_type"]);self.title.setText(row["title"]);self.status.setCurrentText(row["status"]);self.body.setPlainText(row["body"])
        else:self.status.setCurrentText("Working")
    def values(self):return {"draft_type":self.kind.currentText(),"title":self.title.text().strip(),"status":self.status.currentText(),"body":self.body.toPlainText()}

class EvidenceLinkDialog(QDialog):
    def __init__(self,conn,case_id,parent=None):
        super().__init__(parent);self.setWindowTitle("Connect evidence to a party or issue")
        ev,parties,issues=evidence_link_options(conn,case_id);layout=QVBoxLayout(self);form=QFormLayout()
        self.evidence=QComboBox()
        for r in ev:self.evidence.addItem(r["evidence_title"],r["evidence_id"])
        self.party=QComboBox();self.party.addItem("No party link",None)
        for r in parties:self.party.addItem(f"{r['party_name']} — {r['role']}",r["party_id"])
        self.issue=QComboBox();self.issue.addItem("No issue link",None)
        for r in issues:self.issue.addItem(r["issue_title"],r["issue_id"])
        self.note=QLineEdit()
        form.addRow("Evidence item",self.evidence);form.addRow("Related party",self.party);form.addRow("Related legal issue",self.issue);form.addRow("Connection note",self.note)
        layout.addLayout(form);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def values(self):return self.evidence.currentData(),self.party.currentData(),self.issue.currentData(),self.note.text().strip()

class RevenueDraftingPage(QWidget):
    def __init__(self,conn):
        super().__init__();self.conn=conn
        root=QVBoxLayout(self);title=QLabel("Revenue Case Document & Drafting Studio");title.setObjectName("pageTitle");root.addWidget(title)
        intro=QLabel("Prepare working drafts, connect evidence to parties and legal issues, and export a consolidated case-preparation report. Drafts are user-authored and are not verified legal forms.")
        intro.setWordWrap(True);intro.setObjectName("muted");root.addWidget(intro)
        row=QHBoxLayout();row.addWidget(QLabel("Select case:"));self.case=QComboBox();self.case.currentIndexChanged.connect(self.refresh);row.addWidget(self.case,1)
        b=QPushButton("Refresh cases");b.clicked.connect(self.load_cases);row.addWidget(b);root.addLayout(row)
        self.tabs=QTabWidgetCompat();root.addWidget(self.tabs,1)
        draft_page=QWidget();dl=QVBoxLayout(draft_page);dr=QHBoxLayout()
        for label,fn in [("New draft",self.new_draft),("Edit selected",self.edit_draft),("Export selected draft",self.export_draft),("Delete selected",self.remove_draft)]:
            b=QPushButton(label);b.clicked.connect(fn);dr.addWidget(b)
        dr.addStretch(1);dl.addLayout(dr);self.drafts=self.make_table(["ID","Type","Title","Status","Version","Last updated"]);dl.addWidget(self.drafts,1);self.tabs.addTab(draft_page,"Drafting Workspace")
        links_page=QWidget();ll=QVBoxLayout(links_page);lr=QHBoxLayout()
        b=QPushButton("Connect evidence");b.clicked.connect(self.new_link);lr.addWidget(b)
        b=QPushButton("Remove selected connection");b.clicked.connect(self.remove_link);lr.addWidget(b);lr.addStretch(1);ll.addLayout(lr)
        self.links=self.make_table(["Link ID","Evidence","Related party","Legal issue","Connection note"]);ll.addWidget(self.links,1);self.tabs.addTab(links_page,"Evidence Connections")
        report_page=QWidget();rl=QVBoxLayout(report_page)
        note=QLabel("Exports a readable text report containing case details, parties, property, chronology, evidence, issue notes and draft register. It does not export the full draft text.")
        note.setWordWrap(True);rl.addWidget(note)
        b=QPushButton("Export case preparation report (.txt)");b.clicked.connect(self.export_report);rl.addWidget(b);rl.addStretch(1);self.tabs.addTab(report_page,"Case Reports")
        assembly=QWidget(); al=QVBoxLayout(assembly)
        anote=QLabel("Convert an issue-led research bundle into an editable working draft. Issue facts, arguments and source pinpoints are inserted as a scaffold; no legal conclusions or prescribed forms are generated.")
        anote.setWordWrap(True);anote.setObjectName("muted");al.addWidget(anote)
        arow=QHBoxLayout();self.research_bundle=QComboBox();self.research_bundle.currentIndexChanged.connect(self.preview_research_bundle)
        self.assembly_type=QComboBox();self.assembly_type.addItems(DRAFT_TYPES)
        self.assembly_title=QLineEdit();self.assembly_title.setPlaceholderText("Draft title")
        arow.addWidget(QLabel("Research bundle"));arow.addWidget(self.research_bundle,2);arow.addWidget(QLabel("Draft type"));arow.addWidget(self.assembly_type);arow.addWidget(self.assembly_title,2);al.addLayout(arow)
        ab=QHBoxLayout()
        b=QPushButton("Refresh research bundles");b.clicked.connect(self.refresh_research_bundles);ab.addWidget(b)
        b=QPushButton("Create draft from bundle");b.clicked.connect(self.assemble_research_draft);ab.addWidget(b)
        b=QPushButton("Export selected draft with source schedule");b.clicked.connect(self.export_draft_with_sources);ab.addWidget(b);ab.addStretch(1);al.addLayout(ab)
        self.assembly_preview=QTextEdit();self.assembly_preview.setReadOnly(True);self.assembly_preview.setPlaceholderText("Select a research bundle to preview its draft scaffold.");al.addWidget(self.assembly_preview,1)
        self.tabs.addTab(assembly,"Research-to-Draft")
        self.load_cases()
    def make_table(self,headers):
        t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);t.setSelectionBehavior(QAbstractItemView.SelectRows);t.setEditTriggers(QAbstractItemView.NoEditTriggers);return t
    def case_id(self):return self.case.currentData()
    def load_cases(self):
        old=self.case.currentData();self.case.blockSignals(True);self.case.clear()
        for r in list_cases(self.conn):self.case.addItem(f"#{r['case_id']} — {r['case_title']}",r["case_id"])
        idx=self.case.findData(old)
        if idx>=0:self.case.setCurrentIndex(idx)
        self.case.blockSignals(False);self.refresh()
    def refresh(self,*args):
        cid=self.case_id()
        if cid is None:
            self.drafts.setRowCount(0);self.links.setRowCount(0);self.refresh_research_bundles();return
        ds=list_drafts(self.conn,cid);self.drafts.setRowCount(len(ds))
        for i,r in enumerate(ds):
            vals=[r["draft_id"],r["draft_type"],r["title"],r["status"],r["version"],r["updated_at"]]
            for j,v in enumerate(vals):self.drafts.setItem(i,j,QTableWidgetItem("" if v is None else str(v)))
        ls=list_evidence_links(self.conn,cid);self.links.setRowCount(len(ls))
        for i,r in enumerate(ls):
            vals=[r["link_id"],r["evidence_title"],r["party_name"] or "",r["issue_title"] or "",r["link_note"]]
            for j,v in enumerate(vals):self.links.setItem(i,j,QTableWidgetItem(str(v or "")))
        self.refresh_research_bundles()
    def refresh_research_bundles(self,*args):
        old=self.research_bundle.currentData();self.research_bundle.blockSignals(True);self.research_bundle.clear()
        cid=self.case_id()
        if cid is not None:
            for r in eligible_bundles(self.conn,cid):
                label=f"#{r['bundle_id']} — {r['title']}" + (" (general)" if r["case_id"] is None else "")
                self.research_bundle.addItem(label,r["bundle_id"])
        idx=self.research_bundle.findData(old)
        if idx>=0:self.research_bundle.setCurrentIndex(idx)
        self.research_bundle.blockSignals(False);self.preview_research_bundle()
    def preview_research_bundle(self,*args):
        bid=self.research_bundle.currentData()
        if bid is None:self.assembly_preview.clear();return
        try:
            from app.services.legal_draft_assembly import draft_package
            body,sources,bundle=draft_package(self.conn,bid)
            self.assembly_preview.setPlainText(body+"\\n\\n[Preview includes "+str(len(sources))+" source-link entries. The saved draft retains a separate source schedule.]")
            if not self.assembly_title.text().strip():self.assembly_title.setText(bundle["title"]+" — Working Draft")
        except Exception as e:self.assembly_preview.setPlainText("Could not preview bundle: "+str(e))
    def assemble_research_draft(self):
        cid=self.case_id();bid=self.research_bundle.currentData()
        if cid is None or bid is None:
            QMessageBox.information(self,"Select records","Select a case and an eligible research bundle first.");return
        try:
            did=create_draft_from_bundle(self.conn,cid,bid,self.assembly_type.currentText(),self.assembly_title.text().strip() or "Research-based working draft")
            self.refresh();QMessageBox.information(self,"Draft created",f"Created draft #{did}. It is editable in the Drafting Workspace and retains source-link snapshots.")
        except Exception as e:QMessageBox.warning(self,"Could not assemble draft",str(e))
    def export_draft_with_sources(self):
        did=self.selected_id(self.drafts)
        if did is None:
            QMessageBox.information(self,"Select draft","Select a draft in Drafting Workspace first.");return
        row=get_draft(self.conn,did);safe="".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in row["title"]).strip().replace(" ","-") or "draft"
        path,_=QFileDialog.getSaveFileName(self,"Export draft and source schedule",safe+"-with-sources.txt","Text files (*.txt)")
        if path:
            try:
                Path(path).write_text(build_draft_export(self.conn,did),encoding="utf-8")
                QMessageBox.information(self,"Exported",f"Saved draft and source schedule to:\\n{path}")
            except Exception as e:QMessageBox.warning(self,"Export failed",str(e))
    def selected_id(self,table):
        row=table.currentRow()
        if row<0:return None
        return int(table.item(row,0).text())
    def new_draft(self):
        cid=self.case_id()
        if cid is None:QMessageBox.information(self,"Select a case","Create a case in My Revenue Cases first.");return
        d=DraftDialog(self)
        if d.exec():
            try:save_draft(self.conn,cid,d.values());self.refresh()
            except Exception as e:QMessageBox.warning(self,"Could not save draft",str(e))
    def edit_draft(self):
        did=self.selected_id(self.drafts)
        if did is None:return
        row=get_draft(self.conn,did);d=DraftDialog(self,row)
        if d.exec():
            try:save_draft(self.conn,self.case_id(),d.values(),did);self.refresh()
            except Exception as e:QMessageBox.warning(self,"Could not update draft",str(e))
    def export_draft(self):
        did=self.selected_id(self.drafts)
        if did is None:return
        row=get_draft(self.conn,did)
        safe="".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in row["title"]).strip().replace(" ","-") or "draft"
        path,_=QFileDialog.getSaveFileName(self,"Export draft",safe+".txt","Text files (*.txt)")
        if not path:return
        try:
            content=f"{row['title']}\\n{'='*len(row['title'])}\\nType: {row['draft_type']}\\nStatus: {row['status']}\\nVersion: {row['version']}\\n\\n{row['body']}\\n"
            Path(path).write_text(content,encoding="utf-8")
            QMessageBox.information(self,"Draft exported",f"Saved draft to:\\n{path}")
        except Exception as e:QMessageBox.warning(self,"Export failed",str(e))
    def remove_draft(self):
        did=self.selected_id(self.drafts)
        if did is None:return
        if QMessageBox.question(self,"Delete draft","Delete the selected draft?") == QMessageBox.Yes:
            delete_draft(self.conn,did);self.refresh()
    def new_link(self):
        cid=self.case_id()
        if cid is None:return
        ev,parties,issues=evidence_link_options(self.conn,cid)
        if not ev:QMessageBox.information(self,"No evidence","Add evidence in My Revenue Cases first.");return
        if not parties and not issues:QMessageBox.information(self,"No targets","Add at least one party or legal issue in My Revenue Cases first.");return
        d=EvidenceLinkDialog(self.conn,cid,self)
        if d.exec():
            eid,pid,iid,note=d.values()
            try:add_evidence_link(self.conn,eid,pid,iid,note);self.refresh()
            except Exception as e:QMessageBox.warning(self,"Could not connect evidence",str(e))
    def remove_link(self):
        lid=self.selected_id(self.links)
        if lid is None:return
        delete_evidence_link(self.conn,lid);self.refresh()
    def export_report(self):
        cid=self.case_id()
        if cid is None:QMessageBox.information(self,"Select a case","No case selected.");return
        name=f"case-{cid}-preparation-report.txt"
        path,_=QFileDialog.getSaveFileName(self,"Export case report",name,"Text files (*.txt)")
        if not path:return
        try:
            Path(path).write_text(build_case_report(self.conn,cid),encoding="utf-8")
            self.conn.execute("INSERT INTO revenue_case_report_log(case_id,report_type,exported_path) VALUES(?,?,?)",(cid,"Case preparation report",path));self.conn.commit()
            QMessageBox.information(self,"Report exported",f"Saved report to:\n{path}")
        except Exception as e:QMessageBox.warning(self,"Export failed",str(e))

from PySide6.QtWidgets import QTabWidget as QTabWidgetCompat
