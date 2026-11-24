from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,
    QTableWidget,QTableWidgetItem,QHeaderView,QComboBox,QDialog,QFormLayout,QTextEdit,
    QDialogButtonBox,QMessageBox,QInputDialog,QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from app.database.repositories import JudgmentRepository
from app.services.judgment_research_service import JudgmentResearchService

class JudgmentEntryDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle("Add judgment to local research library")
        self.fields={}
        layout=QVBoxLayout(self); form=QFormLayout()
        specs=[
            ("case_title","Case title",False),("case_number","Case number",False),
            ("citation","Reported citation (if verified)",False),("decision_date","Decision date YYYY-MM-DD",False),
            ("court_name","Court name",False),("judge_names","Judge(s)",False),
            ("petitioner","Petitioner / appellant",False),("respondent","Respondent",False),
            ("official_url","Official judgment URL",False),("subject_keywords","Subject keywords (; separated)",False),
            ("full_text","Judgment text (optional)",True)
        ]
        for key,label,multi in specs:
            widget=QTextEdit() if multi else QLineEdit()
            if multi: widget.setMinimumHeight(150)
            self.fields[key]=widget; form.addRow(label,widget)
        layout.addLayout(form)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
    def values(self):
        return {k:(w.toPlainText().strip() if isinstance(w,QTextEdit) else w.text().strip())
                for k,w in self.fields.items()}

class JudgmentDetailDialog(QDialog):
    def __init__(self, judgment, service, parent=None):
        super().__init__(parent); self.judgment=judgment; self.service=service
        self.setWindowTitle(f"Judgment Research — {judgment['case_title']}")
        self.resize(950,700)
        layout=QVBoxLayout(self)
        meta=[]
        for label,key in [("Citation","citation"),("Case number","case_number"),("Court","court_name"),
                          ("Decision date","decision_date"),("Judge(s)","judge_names"),
                          ("Parties","petitioner")]:
            value=judgment[key] or ""
            if key=="petitioner" and judgment["respondent"]:
                value += " v. " + judgment["respondent"]
            meta.append(f"{label}: {value}")
        lbl=QLabel("\n".join(meta)); lbl.setWordWrap(True); layout.addWidget(lbl)
        self.text=QTextEdit(); self.text.setReadOnly(True)
        self.text.setPlainText(judgment["full_text"] or "No judgment text has been imported. Use the official source link, if available.")
        layout.addWidget(self.text,1)
        self.references=QLabel(); self.references.setWordWrap(True); layout.addWidget(self.references)
        self.refresh_references()
        buttons=QHBoxLayout()
        add_topic=QPushButton("Add subject")
        add_topic.clicked.connect(self.add_topic); buttons.addWidget(add_topic)
        add_section=QPushButton("Add statutory reference")
        add_section.clicked.connect(self.add_section); buttons.addWidget(add_section)
        relation=QPushButton("Link related judgment")
        relation.clicked.connect(self.add_relation); buttons.addWidget(relation)
        if judgment["official_url"]:
            open_btn=QPushButton("Open official source")
            open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(judgment["official_url"])))
            buttons.addWidget(open_btn)
        layout.addLayout(buttons)
        close=QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); close.accepted.connect(self.accept)
        layout.addWidget(close)

    def refresh_references(self):
        refs=self.service.statutory_references(self.judgment["judgment_id"])
        rels=self.service.related(self.judgment["judgment_id"])
        lines=["Statutory references:"]
        lines += [f"• {r['act_name']}, section {r['section_number']} [{r['verification_status']}]" for r in refs] or ["• None recorded"]
        lines += ["Related judgments:"]
        lines += [f"• {r['related_title']} — {r['relation_type']} [{r['verification_status']}]" for r in rels] or ["• None recorded"]
        self.references.setText("\n".join(lines))

    def add_topic(self):
        topic,ok=QInputDialog.getText(self,"Add subject","Subject / legal issue:")
        if ok and topic.strip():
            try: self.service.add_topic(self.judgment["judgment_id"],topic); self.refresh_references()
            except Exception as e: QMessageBox.warning(self,"Could not add",str(e))

    def add_section(self):
        act,ok=QInputDialog.getText(self,"Statutory reference","Act / legislation name:")
        if not ok or not act.strip(): return
        section,ok=QInputDialog.getText(self,"Statutory reference","Section / provision:")
        if not ok or not section.strip(): return
        context,ok=QInputDialog.getText(self,"Statutory reference","Context or paragraph (optional):")
        if not ok: context=""
        try:
            self.service.add_statutory_reference(self.judgment["judgment_id"],act,section,context)
            self.refresh_references()
        except Exception as e: QMessageBox.warning(self,"Could not add",str(e))

    def add_relation(self):
        target,ok=QInputDialog.getInt(self,"Link judgment","Target judgment database ID:",1,1,99999999)
        if not ok:return
        relation,ok=QInputDialog.getItem(self,"Relationship type","Relationship:",
            ["Followed","Distinguished","Applied","Referred","Overruled","Reversed","Related"],0,False)
        if not ok:return
        notes,ok=QInputDialog.getText(self,"Relationship note","Explain the relationship and source:")
        if not ok: notes=""
        try:
            self.service.add_relation(self.judgment["judgment_id"],target,relation,notes)
            self.refresh_references()
        except Exception as e: QMessageBox.warning(self,"Could not link",str(e))

class JudgmentResearchPage(QWidget):
    def __init__(self,conn):
        super().__init__(); self.conn=conn
        self.repo=JudgmentRepository(conn); self.service=JudgmentResearchService(conn)
        layout=QVBoxLayout(self)
        title=QLabel("Judgment Research Engine"); title.setObjectName("pageTitle"); layout.addWidget(title)
        hint=QLabel("Search locally imported judgments. Online coverage is not automatic; verify every citation and judicial treatment.")
        hint.setWordWrap(True); hint.setObjectName("muted"); layout.addWidget(hint)
        searchrow=QHBoxLayout()
        self.query=QLineEdit(); self.query.setPlaceholderText("Search case title, citation, parties, judge, subject or judgment text")
        self.query.returnPressed.connect(self.search); searchrow.addWidget(self.query,1)
        self.search_btn=QPushButton("Search"); self.search_btn.clicked.connect(self.search); searchrow.addWidget(self.search_btn)
        add=QPushButton("Add judgment"); add.clicked.connect(self.add_judgment); searchrow.addWidget(add)
        layout.addLayout(searchrow)
        filters=QHBoxLayout()
        self.court=QComboBox(); self.court.addItem("All"); self.court.addItems(self.repo.courts()); filters.addWidget(QLabel("Court")); filters.addWidget(self.court)
        self.year=QLineEdit(); self.year.setPlaceholderText("Year"); self.year.setMaximumWidth(90); filters.addWidget(self.year)
        self.topic=QComboBox(); self.topic.addItem("All")
        for t in self.repo.topics(): self.topic.addItem(t,t.casefold())
        filters.addWidget(QLabel("Subject")); filters.addWidget(self.topic)
        self.verification=QComboBox(); self.verification.addItems(["All","unverified","official_verified","secondary_source","sample_only"])
        filters.addWidget(QLabel("Source status")); filters.addWidget(self.verification)
        refresh=QPushButton("Refresh filters"); refresh.clicked.connect(self.refresh_filters); filters.addWidget(refresh)
        layout.addLayout(filters)
        self.results=QTableWidget(0,7)
        self.results.setHorizontalHeaderLabels(["ID","Case title","Citation","Date","Court","Judge(s)","Verification"])
        self.results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results.setAlternatingRowColors(True); self.results.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results.cellDoubleClicked.connect(self.open_selected)
        layout.addWidget(self.results,1)
        self.status=QLabel("Enter a search phrase or apply filters. Double-click a result to inspect it.")
        self.status.setObjectName("muted"); layout.addWidget(self.status)

    def refresh_filters(self):
        current=self.court.currentText()
        self.court.clear(); self.court.addItem("All"); self.court.addItems(self.repo.courts())
        idx=self.court.findText(current)
        if idx>=0:self.court.setCurrentIndex(idx)
        topic=self.topic.currentText()
        self.topic.clear(); self.topic.addItem("All")
        for t in self.repo.topics():self.topic.addItem(t,t.casefold())
        idx=self.topic.findText(topic)
        if idx>=0:self.topic.setCurrentIndex(idx)
        self.search()

    def search(self):
        year=self.year.text().strip()
        if year and (not year.isdigit() or len(year)!=4):
            QMessageBox.warning(self,"Invalid year","Enter a four-digit year."); return
        topic=self.topic.currentData()
        if self.topic.currentText()=="All":topic="All"
        rows=self.service.search(self.query.text(),self.court.currentText(),year,topic,
                                 self.verification.currentText())
        self.results.setRowCount(len(rows))
        for r,row in enumerate(rows):
            vals=[row["judgment_id"],row["case_title"],row["citation"],row["decision_date"],
                  row["court_name"],row["judge_names"],row["verification_status"]]
            for c,val in enumerate(vals):
                item=QTableWidgetItem("" if val is None else str(val))
                if c==0:item.setData(Qt.UserRole,row["judgment_id"])
                self.results.setItem(r,c,item)
        self.status.setText(f"{len(rows)} local judgment record(s). This is not a live search of court websites.")

    def add_judgment(self):
        dialog=JudgmentEntryDialog(self)
        if dialog.exec():
            v=dialog.values()
            if not v["case_title"]:
                QMessageBox.warning(self,"Required","Case title is required."); return
            if v["decision_date"] and len(v["decision_date"])!=10:
                QMessageBox.warning(self,"Date format","Use YYYY-MM-DD or leave blank."); return
            try:
                self.repo.create(**v)
                self.refresh_filters()
                QMessageBox.information(self,"Saved","Judgment metadata saved as unverified. Confirm source and citation before relying on it.")
            except Exception as e:QMessageBox.critical(self,"Save failed",str(e))

    def open_selected(self,row,column):
        item=self.results.item(row,0)
        if not item:return
        judgment=self.repo.get(int(item.text()))
        if judgment:
            JudgmentDetailDialog(judgment,self.service,self).exec()
            self.refresh_filters()
