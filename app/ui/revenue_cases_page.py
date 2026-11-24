from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QComboBox,
    QTableWidget,QTableWidgetItem,QHeaderView,QTabWidget,QDialog,QFormLayout,QTextEdit,QDialogButtonBox,
    QMessageBox,QAbstractItemView)
from app.services.revenue_case_service import (CASE_TYPES,CASE_STATUSES,PARTY_ROLES,list_cases,create_case,
    update_case,case_detail,add_party,parties,add_property,properties,add_event,events,add_evidence,
    evidence,add_issue,issues,delete_case)

class CaseForm(QDialog):
    def __init__(self,parent=None,row=None):
        super().__init__(parent); self.setWindowTitle("Revenue case details"); self.widgets={}
        layout=QVBoxLayout(self); form=QFormLayout()
        fields=[
            ("case_title","Case title",False),("case_type","Case type",False),("case_number","Case / diary number",False),
            ("authority","Revenue authority / court",False),("district","District",False),("tehsil","Tehsil",False),
            ("village","Village",False),("filing_date","Filing date YYYY-MM-DD",False),("status","Status",False),
            ("next_hearing_date","Next hearing YYYY-MM-DD",False),("priority","Priority",False),
            ("case_summary","Case summary / relief sought",True),("strategy_notes","Preparation notes (private)",True)]
        for key,label,multi in fields:
            w=QTextEdit() if multi else (QComboBox() if key in ("case_type","status","priority") else QLineEdit())
            if isinstance(w,QComboBox):
                w.addItems(CASE_TYPES if key=="case_type" else CASE_STATUSES if key=="status" else ["Low","Normal","High","Urgent"])
            if multi:w.setMinimumHeight(65)
            self.widgets[key]=w; form.addRow(label,w)
        layout.addLayout(form)
        if row:
            for k,w in self.widgets.items():
                value=row[k] or ""
                if isinstance(w,QTextEdit):w.setPlainText(str(value))
                elif isinstance(w,QComboBox):
                    idx=w.findText(str(value))
                    if idx>=0:w.setCurrentIndex(idx)
                else:w.setText(str(value))
        else:
            self.widgets["case_type"].setCurrentText("Other")
            self.widgets["status"].setCurrentText("Preparing")
            self.widgets["priority"].setCurrentText("Normal")
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def values(self):
        return {k:(w.toPlainText().strip() if isinstance(w,QTextEdit) else w.currentText() if isinstance(w,QComboBox) else w.text().strip()) for k,w in self.widgets.items()}

class RecordDialog(QDialog):
    def __init__(self,title,fields,parent=None,choices=None):
        super().__init__(parent);self.setWindowTitle(title);self.widgets={}
        layout=QVBoxLayout(self);form=QFormLayout()
        for key,label,multi,default in fields:
            if choices and key in choices:
                w=QComboBox()
                for text,data in choices[key]:w.addItem(text,data)
            else:w=QTextEdit() if multi else QLineEdit()
            if isinstance(w,QTextEdit):w.setMinimumHeight(75);w.setPlainText(default or "")
            elif isinstance(w,QLineEdit):w.setText(default or "")
            elif default:
                idx=w.findText(default)
                if idx>=0:w.setCurrentIndex(idx)
            self.widgets[key]=w;form.addRow(label,w)
        layout.addLayout(form);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def values(self):
        out={}
        for k,w in self.widgets.items():
            if isinstance(w,QTextEdit):out[k]=w.toPlainText().strip()
            elif isinstance(w,QComboBox):out[k]=w.currentData()
            else:out[k]=w.text().strip()
        return out

class RevenueCasesPage(QWidget):
    def __init__(self,conn):
        super().__init__();self.conn=conn;self.current_case_id=None
        root=QVBoxLayout(self)
        title=QLabel("My Revenue Cases");title.setObjectName("pageTitle");root.addWidget(title)
        intro=QLabel("Private local case register for land and revenue matters. Keep dates in YYYY-MM-DD format. Verify every legal deadline independently; this register is not a limitation calculator.")
        intro.setWordWrap(True);intro.setObjectName("muted");root.addWidget(intro)
        row=QHBoxLayout();self.query=QLineEdit();self.query.setPlaceholderText("Search case, number, village, tehsil or authority...")
        self.query.returnPressed.connect(self.refresh_cases);row.addWidget(self.query,1)
        self.status=QComboBox();self.status.addItems(["All"]+CASE_STATUSES);self.status.currentTextChanged.connect(self.refresh_cases);row.addWidget(self.status)
        for label,fn in [("New case",self.new_case),("Edit selected",self.edit_case),("Delete selected",self.remove_case),("Refresh",self.refresh_cases)]:
            b=QPushButton(label);b.clicked.connect(fn);row.addWidget(b)
        root.addLayout(row)
        self.case_table=QTableWidget(0,8);self.case_table.setHorizontalHeaderLabels(["ID","Case title","Type","Authority","Village","Status","Next hearing","Priority"])
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);self.case_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.case_table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.case_table.itemSelectionChanged.connect(self.case_selected)
        root.addWidget(self.case_table,1)
        self.tabs=QTabWidget();root.addWidget(self.tabs,2)
        self.party_table=self.table(["ID","Party","Role","Representative","Address / notes"])
        self.property_table=self.table(["ID","Village","Hadbast","Jamabandi","Khata","Khatauni","Khasra","Area","Share"])
        self.event_table=self.table(["ID","Date","Type","Event","Details","Next action"])
        self.evidence_table=self.table(["ID","Evidence","Type","Linked document","Reference","Verification","Relevance"])
        self.issue_table=self.table(["ID","Issue","Legal question","Status","Relevant law"])
        self.tabs.addTab(self.make_detail_tab(self.party_table,"Add party",self.add_party),"Parties")
        self.tabs.addTab(self.make_detail_tab(self.property_table,"Add land / property",self.add_property),"Land & Property")
        self.tabs.addTab(self.make_detail_tab(self.event_table,"Add chronology / hearing",self.add_event),"Chronology & Hearings")
        self.tabs.addTab(self.make_detail_tab(self.evidence_table,"Add evidence item",self.add_evidence),"Evidence")
        self.tabs.addTab(self.make_detail_tab(self.issue_table,"Add legal issue",self.add_issue),"Issues & Arguments")
        self.refresh_cases()
    def table(self,headers):
        t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setSelectionBehavior(QAbstractItemView.SelectRows);t.setEditTriggers(QAbstractItemView.NoEditTriggers);t.setAlternatingRowColors(True);return t
    def make_detail_tab(self,table,button_text,callback):
        page=QWidget();layout=QVBoxLayout(page);row=QHBoxLayout();b=QPushButton(button_text);b.clicked.connect(callback);row.addWidget(b);row.addStretch(1);layout.addLayout(row);layout.addWidget(table,1);return page
    def selected_case_id(self):
        row=self.case_table.currentRow()
        if row<0:return None
        try:return int(self.case_table.item(row,0).text())
        except Exception:return None
    def refresh_cases(self):
        rows=list_cases(self.conn,self.query.text(),self.status.currentText())
        self.case_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            vals=[r["case_id"],r["case_title"],r["case_type"],r["authority"],r["village"],r["status"],r["next_hearing_date"],r["priority"]]
            for j,v in enumerate(vals):self.case_table.setItem(i,j,QTableWidgetItem("" if v is None else str(v)))
        if rows:
            self.case_table.selectRow(0)
        else:
            self.current_case_id=None;self.clear_details()
    def case_selected(self):
        cid=self.selected_case_id()
        if cid is None:return
        self.current_case_id=cid;self.refresh_details()
    def clear_details(self):
        for t in [self.party_table,self.property_table,self.event_table,self.evidence_table,self.issue_table]:t.setRowCount(0)
    def fill(self,table,rows,keys):
        table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,k in enumerate(keys):
                v=r[k]
                table.setItem(i,j,QTableWidgetItem("" if v is None else str(v)))
    def refresh_details(self):
        cid=self.current_case_id
        if cid is None:self.clear_details();return
        self.fill(self.party_table,parties(self.conn,cid),["party_id","party_name","role","representative","address"])
        self.fill(self.property_table,properties(self.conn,cid),["property_id","village","hadbast_number","jamabandi_year","khata_number","khatauni_number","khasra_numbers","area","ownership_share"])
        self.fill(self.event_table,events(self.conn,cid),["event_id","event_date","event_type","title","details","next_action"])
        self.fill(self.evidence_table,evidence(self.conn,cid),["evidence_id","evidence_title","evidence_type","linked_document","document_reference","verification_status","relevance_notes"])
        self.fill(self.issue_table,issues(self.conn,cid),["issue_id","issue_title","legal_question","status","relevant_law"])
    def require_case(self):
        if self.current_case_id is None:
            QMessageBox.information(self,"Select a case","Create or select a case first.");return False
        return True
    def new_case(self):
        d=CaseForm(self)
        if d.exec():
            try:
                cid=create_case(self.conn,d.values());self.refresh_cases()
                for r in range(self.case_table.rowCount()):
                    if int(self.case_table.item(r,0).text())==cid:self.case_table.selectRow(r);break
            except Exception as e:QMessageBox.warning(self,"Could not save case",str(e))
    def edit_case(self):
        cid=self.selected_case_id()
        if cid is None:return
        d=CaseForm(self,case_detail(self.conn,cid))
        if d.exec():
            try:update_case(self.conn,cid,d.values());self.refresh_cases()
            except Exception as e:QMessageBox.warning(self,"Could not update case",str(e))
    def remove_case(self):
        cid=self.selected_case_id()
        if cid is None:return
        answer=QMessageBox.question(self,"Delete case","Delete this case and its parties, property details, events, evidence links and issues? Original documents in the Document Library will not be deleted.")
        if answer==QMessageBox.Yes:
            delete_case(self.conn,cid);self.current_case_id=None;self.refresh_cases()
    def add_party(self):
        if not self.require_case():return
        d=RecordDialog("Add party",[("party_name","Name",False,""),("role","Role",False,"Other"),("representative","Representative / counsel",False,""),("address","Address / identifying details",True,""),("contact_notes","Contact notes",True,"")],self,{"role":[(x,x) for x in PARTY_ROLES]})
        if d.exec():
            v=d.values()
            if not v["party_name"]:QMessageBox.warning(self,"Required","Party name is required.");return
            add_party(self.conn,self.current_case_id,v);self.refresh_details()
    def add_property(self):
        if not self.require_case():return
        fields=[("village","Village",False,""),("tehsil","Tehsil",False,""),("district","District",False,""),("hadbast_number","Hadbast number",False,""),("jamabandi_year","Jamabandi year",False,""),("khata_number","Khata number",False,""),("khatauni_number","Khatauni number",False,""),("khasra_numbers","Khasra numbers",False,""),("area","Area / units",False,""),("ownership_share","Ownership share",False,""),("land_description","Land description / boundaries",True,"")]
        d=RecordDialog("Add land / property details",fields,self)
        if d.exec():
            add_property(self.conn,self.current_case_id,d.values());self.refresh_details()
    def add_event(self):
        if not self.require_case():return
        d=RecordDialog("Add chronology / hearing item",[("event_date","Date YYYY-MM-DD",False,""),("event_type","Type",False,"Hearing"),("title","Event / order / filing",False,""),("details","What happened / order summary",True,""),("next_action","Next action / due date",True,"")],self)
        if d.exec():
            v=d.values()
            if not v["title"]:QMessageBox.warning(self,"Required","Event title is required.");return
            add_event(self.conn,self.current_case_id,v);self.refresh_details()
    def add_evidence(self):
        if not self.require_case():return
        docs=self.conn.execute("SELECT document_id,document_title FROM documents ORDER BY document_title").fetchall()
        choices={"document_id":[("Not linked",None)]+[(f"#{r['document_id']} — {r['document_title']}",r["document_id"]) for r in docs],
            "verification_status":[(x,x) for x in ["unverified","source_checked","copy_compared","disputed"]]}
        d=RecordDialog("Add evidence item",[("evidence_title","Evidence / record title",False,""),("evidence_type","Type",False,"Revenue record"),("document_id","Link existing document",False,""),("document_reference","Page / entry / mutation number",False,""),("verification_status","Verification",False,"unverified"),("relevance_notes","Relevance / evidentiary notes",True,"")],self,choices)
        if d.exec():
            v=d.values()
            if not v["evidence_title"]:QMessageBox.warning(self,"Required","Evidence title is required.");return
            add_evidence(self.conn,self.current_case_id,v);self.refresh_details()
    def add_issue(self):
        if not self.require_case():return
        d=RecordDialog("Add legal issue / argument",[("issue_title","Issue",False,""),("facts","Relevant facts",True,""),("legal_question","Legal question",True,""),("proposed_argument","Proposed argument / submission",True,""),("relevant_law","Act / section / rule / judgment references",True,""),("status","Status",False,"Open")],self)
        if d.exec():
            v=d.values()
            if not v["issue_title"]:QMessageBox.warning(self,"Required","Issue title is required.");return
            add_issue(self.conn,self.current_case_id,v);self.refresh_details()
