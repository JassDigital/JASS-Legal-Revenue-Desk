from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTableWidget,
 QTableWidgetItem,QHeaderView,QAbstractItemView,QTabWidget,QFrame,QGridLayout,QMessageBox)
from app.services.revenue_case_intelligence import (dashboard_summary,upcoming_hearings,
 recorded_deadlines,outstanding_steps,manually_recorded_limitation_reviews)

class RevenueCaseIntelligencePage(QWidget):
    def __init__(self,conn):
        super().__init__();self.conn=conn
        root=QVBoxLayout(self)
        header=QHBoxLayout();title=QLabel("Haryana Revenue Case Intelligence Dashboard");title.setObjectName("pageTitle");header.addWidget(title);header.addStretch(1)
        refresh=QPushButton("Refresh dashboard");refresh.clicked.connect(self.refresh);header.addWidget(refresh);root.addLayout(header)
        intro=QLabel("A consolidated operational view of case progress, hearings, recorded deadlines, preparation tasks, research and draft workload. This dashboard reports entered data; it does not assess legal merits or calculate limitation.")
        intro.setWordWrap(True);intro.setObjectName("muted");root.addWidget(intro)
        self.metrics=QGridLayout();self.metric_labels={}
        metrics=[("total_cases","Total cases"),("active_cases","Active cases"),("upcoming_hearings","Upcoming hearings"),("open_research_issues","Open research issues"),("working_drafts","Working drafts"),("outstanding_steps","Outstanding steps"),("past_recorded_deadlines","Past recorded deadlines"),("unreviewed_evidence","Evidence needing review")]
        for i,(key,label) in enumerate(metrics):
            card=QFrame();card.setObjectName("metricCard");lay=QVBoxLayout(card)
            value=QLabel("0");value.setObjectName("metricValue");caption=QLabel(label);caption.setObjectName("muted")
            lay.addWidget(value);lay.addWidget(caption);self.metric_labels[key]=value;self.metrics.addWidget(card,i//4,i%4)
        root.addLayout(self.metrics)
        self.tabs=QTabWidget();root.addWidget(self.tabs,1)
        page=QWidget();lay=QVBoxLayout(page);self.cases=self._table(["Case ID","Case","Status","Next hearing","Parties","Evidence","Evidence review","Open case issues","Open research issues","Working drafts","Active proceedings","Open steps","Past deadlines"]);lay.addWidget(self.cases);self.tabs.addTab(page,"Case Overview")
        page=QWidget();lay=QVBoxLayout(page);self.hearings=self._table(["Date","Case","Case number","Authority","Status"]);lay.addWidget(self.hearings);self.tabs.addTab(page,"Upcoming Hearings")
        page=QWidget();lay=QVBoxLayout(page)
        note=QLabel("Deadlines shown here are dates manually recorded in proceeding events. Past dates are flagged for review only; they are not findings that a legal deadline has expired.")
        note.setWordWrap(True);note.setObjectName("muted");lay.addWidget(note)
        self.deadlines=self._table(["Deadline","Case","Proceeding","Event","Next action","Source reference","Status"]);lay.addWidget(self.deadlines);self.tabs.addTab(page,"Recorded Deadlines")
        page=QWidget();lay=QVBoxLayout(page);self.steps=self._table(["Target date","Case","Proceeding","Preparation step","Status","Responsible","Source reference","Verification"]);lay.addWidget(self.steps);self.tabs.addTab(page,"Outstanding Preparation")
        page=QWidget();lay=QVBoxLayout(page)
        note=QLabel("Limitation dates below are entered manually in Procedure Assistant. A date is not independently calculated or verified by this dashboard. Confirm the trigger, applicable provision, exclusions, extensions and forum-specific rules with current authoritative sources.")
        note.setWordWrap(True);note.setObjectName("notice");lay.addWidget(note)
        self.limitation=self._table(["Entered review date","Case","Proceeding","Start date entered","Period note","Source reference","Reviewed by","Review date","Caveat"]);lay.addWidget(self.limitation);self.tabs.addTab(page,"Limitation Review Register")
        self.refresh()
    def _table(self,headers):
        table=QTableWidget(0,len(headers));table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows);table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True);return table
    def _fill(self,table,rows,columns):
        table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,key in enumerate(columns):
                value=row[key] if key in row.keys() else ""
                item=QTableWidgetItem("" if value is None else str(value))
                table.setItem(i,j,item)
    def refresh(self):
        try:
            summary=dashboard_summary(self.conn)
            for key,label in self.metric_labels.items():label.setText(str(summary[key]))
            self._fill(self.cases,summary["cases"],["case_id","case_title","status","next_hearing_date","party_count","evidence_count","evidence_review_count","open_case_issues","open_research_issues","working_drafts","active_proceedings","outstanding_steps","past_recorded_deadlines"])
            self._fill(self.hearings,upcoming_hearings(self.conn),["next_hearing_date","case_title","case_number","authority","status"])
            self._fill(self.deadlines,recorded_deadlines(self.conn),["deadline_date","case_title","proceeding_type","title","next_action","source_reference","status"])
            self._fill(self.steps,outstanding_steps(self.conn),["target_date","case_title","proceeding_type","step_title","step_status","responsible_person","source_reference","verification_status"])
            self._fill(self.limitation,manually_recorded_limitation_reviews(self.conn),["limitation_due_date","case_title","proceeding_type","limitation_start_date","limitation_period_note","limitation_source_reference","limitation_reviewed_by","limitation_reviewed_date","limitation_caveat"])
        except Exception as exc:
            QMessageBox.warning(self,"Dashboard refresh failed",str(exc))
