from pathlib import Path
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QTableWidget,
 QTableWidgetItem,QHeaderView,QAbstractItemView,QDialog,QFormLayout,QLineEdit,QTextEdit,QDialogButtonBox,
 QMessageBox,QFileDialog,QTabWidget)
from app.services.revenue_case_service import list_cases
from app.services.revenue_procedure_service import (PROCEEDING_TYPES,STATUSES,STAGES,STEP_STATUSES,VERIFICATION,
 list_proceedings,create_proceeding,get_proceeding,update_proceeding,delete_proceeding,steps,add_step,update_step,
 delete_step,events,add_event,delete_event,apply_template,build_proceeding_report)

class ProcedureForm(QDialog):
 def __init__(self,title,fields,parent=None,choices=None):
  super().__init__(parent);self.setWindowTitle(title);self.widgets={};layout=QVBoxLayout(self);form=QFormLayout()
  for key,label,kind,default in fields:
   if choices and key in choices:
    w=QComboBox()
    for text,data in choices[key]:w.addItem(text,data)
   elif kind=="multi":w=QTextEdit();w.setMinimumHeight(65);w.setPlainText(default or "")
   else:w=QLineEdit();w.setText(default or "")
   self.widgets[key]=w;form.addRow(label,w)
  layout.addLayout(form);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
  buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
 def values(self):
  from PySide6.QtWidgets import QTextEdit
  return {k:(w.toPlainText().strip() if isinstance(w,QTextEdit) else w.currentData() if isinstance(w,QComboBox) else w.text().strip()) for k,w in self.widgets.items()}

class ProcedureAssistantPage(QWidget):
 def __init__(self,conn):
  super().__init__();self.conn=conn;root=QVBoxLayout(self)
  title=QLabel("Revenue Case Strategy & Procedure Assistant");title.setObjectName("pageTitle");root.addWidget(title)
  intro=QLabel("Track preparation steps, source references, proceedings, events and user-reviewed limitation information. Checklist items are prompts only. No limitation period, filing deadline, forum or legal requirement is calculated or asserted.")
  intro.setWordWrap(True);intro.setObjectName("muted");root.addWidget(intro)
  row=QHBoxLayout();row.addWidget(QLabel("Filter by case:"));self.case_filter=QComboBox();self.case_filter.currentIndexChanged.connect(self.refresh_proceedings);row.addWidget(self.case_filter,1)
  b=QPushButton("Refresh cases");b.clicked.connect(self.load_cases);row.addWidget(b);root.addLayout(row)
  self.proceeding_table=self.table(["ID","Case","Proceeding","Forum","Reference","Stage","Status","User-entered due date"])
  self.proceeding_table.itemSelectionChanged.connect(self.refresh_details);root.addWidget(self.proceeding_table,2)
  bar=QHBoxLayout()
  for label,fn in [("New proceeding",self.new_proceeding),("Edit selected",self.edit_proceeding),("Delete selected",self.remove_proceeding),("Export working sheet",self.export_report)]:
   b=QPushButton(label);b.clicked.connect(fn);bar.addWidget(b)
  bar.addStretch(1);root.addLayout(bar)
  self.tabs=QTabWidget();root.addWidget(self.tabs,3)
  self.build_steps();self.build_events()
  self.load_cases()
 def table(self,headers):
  t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
  t.setSelectionBehavior(QAbstractItemView.SelectRows);t.setEditTriggers(QAbstractItemView.NoEditTriggers);t.setAlternatingRowColors(True);return t
 def fill(self,t,rows,keys):
  t.setRowCount(len(rows))
  for i,r in enumerate(rows):
   for j,k in enumerate(keys):
    v=r[k];t.setItem(i,j,QTableWidgetItem("" if v is None else str(v)))
 def selected(self,t):
  r=t.currentRow()
  return int(t.item(r,0).text()) if r>=0 else None
 def selected_proceeding(self):return self.selected(self.proceeding_table)
 def build_steps(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  for label,fn in [("Apply generic checklist prompts",self.add_template),("Add step",self.new_step),("Edit selected",self.edit_step),("Delete selected",self.remove_step)]:
   b=QPushButton(label);b.clicked.connect(fn);bar.addWidget(b)
  bar.addStretch(1);l.addLayout(bar);self.step_table=self.table(["ID","Order","Step","Status","Target date","Completed","Source","Verification"]);l.addWidget(self.step_table,1)
  self.tabs.addTab(page,"Preparation Checklist")
 def build_events(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  for label,fn in [("Add event / deadline",self.new_event),("Delete selected",self.remove_event)]:
   b=QPushButton(label);b.clicked.connect(fn);bar.addWidget(b)
  bar.addStretch(1);l.addLayout(bar);self.event_table=self.table(["ID","Date","Type","Title","Deadline","Status","Next action"]);l.addWidget(self.event_table,1)
  self.tabs.addTab(page,"Chronology & Deadlines")
 def load_cases(self):
  old=self.case_filter.currentData();self.case_filter.blockSignals(True);self.case_filter.clear();self.case_filter.addItem("All cases",None)
  for r in list_cases(self.conn):self.case_filter.addItem(f"#{r['case_id']} — {r['case_title']}",r["case_id"])
  idx=self.case_filter.findData(old)
  if idx>=0:self.case_filter.setCurrentIndex(idx)
  self.case_filter.blockSignals(False);self.refresh_proceedings()
 def refresh_proceedings(self,*args):
  cid=self.case_filter.currentData();rows=list_proceedings(self.conn,cid)
  self.fill(self.proceeding_table,rows,["proceeding_id","case_title","proceeding_type","forum_name","case_reference","current_stage","status","limitation_due_date"])
  self.refresh_details()
 def refresh_details(self):
  pid=self.selected_proceeding()
  if pid is None:self.step_table.setRowCount(0);self.event_table.setRowCount(0);return
  self.fill(self.step_table,steps(self.conn,pid),["step_id","step_order","step_title","step_status","target_date","completed_date","source_reference","verification_status"])
  self.fill(self.event_table,events(self.conn,pid),["event_id","event_date","event_type","title","deadline_date","status","next_action"])
 def new_proceeding(self):
  cases=[(f"#{r['case_id']} — {r['case_title']}",r["case_id"]) for r in list_cases(self.conn)]
  if not cases:QMessageBox.information(self,"No cases","Create a case in My Revenue Cases first.");return
  d=ProcedureForm("New revenue proceeding",[
   ("case_id","Case","text",""),("proceeding_type","Proceeding type","text","Mutation proceedings"),("forum_name","Forum / authority","text",""),("case_reference","Case number / reference","text",""),("start_date","Start date YYYY-MM-DD","text",""),("current_stage","Current stage","text","Initial assessment"),("status","Status","text","Working"),
   ("limitation_start_date","Potential limitation starting event/date","text",""),("limitation_period_note","Limitation period / legal note (manual)","multi",""),("limitation_source_reference","Statutory source / case reference","multi",""),("limitation_reviewed_by","Reviewed by","text",""),("limitation_reviewed_date","Review date YYYY-MM-DD","text",""),("limitation_due_date","Due date (manually verified)","text",""),("limitation_caveat","Exclusions, copy date, condonation and caveats","multi",""),("strategy_notes","Strategy / preparation notes","multi","")],self,{
    "case_id":cases,"proceeding_type":[(x,x) for x in PROCEEDING_TYPES],"current_stage":[(x,x) for x in STAGES],"status":[(x,x) for x in STATUSES]})
  if d.exec():
   try:create_proceeding(self.conn,d.values());self.refresh_proceedings()
   except Exception as e:QMessageBox.warning(self,"Could not create",str(e))
 def edit_proceeding(self):
  pid=self.selected_proceeding()
  if pid is None:return
  r=get_proceeding(self.conn,pid)
  d=ProcedureForm("Edit proceeding",[
   ("proceeding_type","Proceeding type","text",r["proceeding_type"]),("forum_name","Forum / authority","text",r["forum_name"]),("case_reference","Case number / reference","text",r["case_reference"]),("start_date","Start date YYYY-MM-DD","text",r["start_date"]),("current_stage","Current stage","text",r["current_stage"]),("status","Status","text",r["status"]),
   ("limitation_start_date","Potential limitation starting event/date","text",r["limitation_start_date"]),("limitation_period_note","Limitation period / legal note (manual)","multi",r["limitation_period_note"]),("limitation_source_reference","Statutory source / case reference","multi",r["limitation_source_reference"]),("limitation_reviewed_by","Reviewed by","text",r["limitation_reviewed_by"]),("limitation_reviewed_date","Review date YYYY-MM-DD","text",r["limitation_reviewed_date"]),("limitation_due_date","Due date (manually verified)","text",r["limitation_due_date"]),("limitation_caveat","Exclusions, copy date, condonation and caveats","multi",r["limitation_caveat"]),("strategy_notes","Strategy / preparation notes","multi",r["strategy_notes"])],self,{
    "proceeding_type":[(x,x) for x in PROCEEDING_TYPES],"current_stage":[(x,x) for x in STAGES],"status":[(x,x) for x in STATUSES]})
  if d.exec():
   try:update_proceeding(self.conn,pid,d.values());self.refresh_proceedings()
   except Exception as e:QMessageBox.warning(self,"Could not update",str(e))
 def remove_proceeding(self):
  pid=self.selected_proceeding()
  if pid is None:return
  if QMessageBox.question(self,"Delete proceeding","Delete this workflow and its checklist/events? The linked case remains.")==QMessageBox.Yes:
   delete_proceeding(self.conn,pid);self.refresh_proceedings()
 def add_template(self):
  pid=self.selected_proceeding()
  if pid is None:return
  r=get_proceeding(self.conn,pid);count=apply_template(self.conn,pid,r["proceeding_type"]);self.refresh_details()
  QMessageBox.information(self,"Checklist prompts",f"Added {count} generic preparation prompts. Confirm each item against the current statute, rules, orders and actual facts before treating it as relevant.")
 def new_step(self):
  pid=self.selected_proceeding()
  if pid is None:return
  d=ProcedureForm("Add preparation step",[("step_order","Order","text","10"),("step_title","Step title","text",""),("description","Description / applicability","multi",""),("step_status","Status","text","Not started"),("target_date","Target date YYYY-MM-DD","text",""),("completed_date","Completed date YYYY-MM-DD","text",""),("responsible_person","Responsible person","text",""),("source_reference","Legal / procedural source reference","multi",""),("verification_status","Source verification","text","unverified"),("notes","Notes","multi","")],self,{"step_status":[(x,x) for x in STEP_STATUSES],"verification_status":[(x,x) for x in VERIFICATION]})
  if d.exec():
   v=d.values()
   try:v["step_order"]=int(v["step_order"] or 0);add_step(self.conn,pid,v);self.refresh_details()
   except Exception as e:QMessageBox.warning(self,"Could not save step",str(e))
 def edit_step(self):
  sid=self.selected(self.step_table)
  if sid is None:return
  r=next((x for x in steps(self.conn,self.selected_proceeding()) if x["step_id"]==sid),None)
  if not r:return
  d=ProcedureForm("Edit preparation step",[("step_order","Order","text",str(r["step_order"])),("step_title","Step title","text",r["step_title"]),("description","Description / applicability","multi",r["description"]),("step_status","Status","text",r["step_status"]),("target_date","Target date YYYY-MM-DD","text",r["target_date"]),("completed_date","Completed date YYYY-MM-DD","text",r["completed_date"]),("responsible_person","Responsible person","text",r["responsible_person"]),("source_reference","Legal / procedural source reference","multi",r["source_reference"]),("verification_status","Source verification","text",r["verification_status"]),("notes","Notes","multi",r["notes"])],self,{"step_status":[(x,x) for x in STEP_STATUSES],"verification_status":[(x,x) for x in VERIFICATION]})
  if d.exec():
   v=d.values()
   try:v["step_order"]=int(v["step_order"] or 0);update_step(self.conn,sid,v);self.refresh_details()
   except Exception as e:QMessageBox.warning(self,"Could not update step",str(e))
 def remove_step(self):
  sid=self.selected(self.step_table)
  if sid is not None:delete_step(self.conn,sid);self.refresh_details()
 def new_event(self):
  pid=self.selected_proceeding()
  if pid is None:return
  d=ProcedureForm("Add proceeding event / deadline",[("event_date","Event date YYYY-MM-DD","text",""),("event_type","Type","text","Hearing"),("title","Event title","text",""),("details","Details / order summary","multi",""),("next_action","Next action","multi",""),("deadline_date","Deadline date YYYY-MM-DD (verified manually)","text",""),("source_reference","Source / order reference","multi",""),("status","Status","text","Open")],self,{"event_type":[(x,x) for x in ["Filing","Hearing","Notice","Order","Inspection","Evidence","Deadline","Other"]],"status":[(x,x) for x in ["Open","Completed","Waiting","Cancelled"]]})
  if d.exec():
   try:add_event(self.conn,pid,d.values());self.refresh_details()
   except Exception as e:QMessageBox.warning(self,"Could not save event",str(e))
 def remove_event(self):
  eid=self.selected(self.event_table)
  if eid is not None:delete_event(self.conn,eid);self.refresh_details()
 def export_report(self):
  pid=self.selected_proceeding()
  if pid is None:return
  path,_=QFileDialog.getSaveFileName(self,"Export procedure working sheet",f"procedure-{pid}.txt","Text files (*.txt)")
  if not path:return
  try:
   Path(path).write_text(build_proceeding_report(self.conn,pid),encoding="utf-8")
   QMessageBox.information(self,"Export complete",f"Saved to:\n{path}")
  except Exception as e:QMessageBox.warning(self,"Export failed",str(e))
