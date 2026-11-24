from pathlib import Path
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QTableWidget,
 QTableWidgetItem,QHeaderView,QAbstractItemView,QDialog,QFormLayout,QLineEdit,QTextEdit,QDialogButtonBox,
 QMessageBox,QDoubleSpinBox,QFileDialog,QTabWidget)
from app.services.revenue_case_service import list_cases
from app.services.revenue_records_service import record_sets
from app.services.revenue_partition_service import (PLAN_STATUSES,list_plans,create_plan,get_plan,update_plan,
 delete_plan,analyse_ownership,list_allocations,add_allocation,delete_allocation,analyse_plan,build_partition_report)

class PartitionForm(QDialog):
 def __init__(self,title,fields,parent=None,choices=None):
  super().__init__(parent);self.setWindowTitle(title);self.widgets={};layout=QVBoxLayout(self);form=QFormLayout()
  for key,label,kind,default in fields:
   if choices and key in choices:
    w=QComboBox()
    for text,data in choices[key]:w.addItem(text,data)
   elif kind=="multi":w=QTextEdit();w.setMinimumHeight(75);w.setPlainText(default or "")
   else:w=QLineEdit();w.setText(default or "")
   self.widgets[key]=w;form.addRow(label,w)
  layout.addLayout(form);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
  buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
 def values(self):
  from PySide6.QtWidgets import QTextEdit
  return {k:(w.toPlainText().strip() if isinstance(w,QTextEdit) else w.currentData() if isinstance(w,QComboBox) else w.text().strip()) for k,w in self.widgets.items()}

class PartitionAnalysisPage(QWidget):
 def __init__(self,conn):
  super().__init__();self.conn=conn;root=QVBoxLayout(self)
  title=QLabel("Haryana Partition & Ownership Analysis");title.setObjectName("pageTitle");root.addWidget(title)
  intro=QLabel("Analyse co-sharer entries and prepare proposed Khasra-wise allocations. Results are arithmetic checks only; they do not determine title, legal shares, possession or whether a partition is fair or legally permissible.")
  intro.setWordWrap(True);intro.setObjectName("muted");root.addWidget(intro)
  self.tabs=QTabWidget();root.addWidget(self.tabs,1)
  self.build_ownership();self.build_plans();self.refresh_all()
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
 def build_ownership(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout();self.record=QComboBox();self.record.currentIndexChanged.connect(self.run_analysis)
  bar.addWidget(QLabel("Source record set:"));bar.addWidget(self.record,1)
  b=QPushButton("Refresh");b.clicked.connect(self.refresh_all);bar.addWidget(b);l.addLayout(bar)
  self.ownership=self.table(["Khasra","Recorded owners","Entry rows","Parcel area (acres)","Share total","Analysis"])
  l.addWidget(self.ownership,1)
  self.owner_summary=self.table(["Co-sharer","Share entries","Calculated entitlement (acres)","Entries without area"])
  l.addWidget(QLabel("Owner summary — sum of entered parcel-area × share fractions (only as complete as source entries)."))
  l.addWidget(self.owner_summary,1)
  self.flags=QLabel("Select a source record set.");self.flags.setWordWrap(True);l.addWidget(self.flags)
  self.tabs.addTab(page,"Ownership Analysis")
 def build_plans(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  for label,fn in [("New partition plan",self.new_plan),("Edit plan details",self.edit_plan),("Delete plan",self.remove_plan),("Refresh",self.refresh_plans)]:
   b=QPushButton(label);b.clicked.connect(fn);bar.addWidget(b)
  bar.addStretch(1);l.addLayout(bar)
  self.plans=self.table(["ID","Plan","Village","Record year","Case","Status","Updated"]);self.plans.itemSelectionChanged.connect(self.refresh_allocations);l.addWidget(self.plans,1)
  sub=QHBoxLayout()
  for label,fn in [("Add proposed allocation",self.new_allocation),("Remove allocation",self.remove_allocation),("Export partition statement",self.export_report)]:
   b=QPushButton(label);b.clicked.connect(fn);sub.addWidget(b)
  sub.addStretch(1);l.addLayout(sub)
  self.allocations=self.table(["ID","Khasra","Co-sharer","Proposed area","Unit","Proposed share","Location / quality notes"]);l.addWidget(self.allocations,1)
  self.plan_flags=QLabel("Select a plan to review proposed allocation totals.");self.plan_flags.setWordWrap(True);l.addWidget(self.plan_flags)
  self.tabs.addTab(page,"Partition Worksheet")
 def refresh_all(self):
  sets=record_sets(self.conn);old=self.record.currentData();self.record.blockSignals(True);self.record.clear()
  for r in sets:self.record.addItem(f"{r['village']} — {r['record_year']} [{r['record_type']}] #{r['record_set_id']}",r["record_set_id"])
  idx=self.record.findData(old)
  if idx>=0:self.record.setCurrentIndex(idx)
  self.record.blockSignals(False);self.run_analysis();self.refresh_plans()
 def run_analysis(self,*args):
  rid=self.record.currentData()
  if rid is None:
   self.ownership.setRowCount(0);self.owner_summary.setRowCount(0);self.flags.setText("No revenue record sets found. Add records in Revenue Records Intelligence.");return
  try:
   rs,rows,owners,flags=analyse_ownership(self.conn,rid)
   self.fill(self.ownership,rows,["khasra","owners","owner_count","parcel_area_acres","share_total","share_status"])
   owner_rows=[{"owner":k,"share_entries":v["share_entries"],"entitlement_acres":round(v["entitlement_acres"],6),"unknown_area_entries":v["unknown_area_entries"]} for k,v in sorted(owners.items())]
   self.fill(self.owner_summary,owner_rows,["owner","share_entries","entitlement_acres","unknown_area_entries"])
   self.flags.setText("Review flags:\n"+("\n".join("• "+x for x in flags) if flags else "No arithmetic flags generated."))
  except Exception as e:QMessageBox.warning(self,"Analysis failed",str(e))
 def selected_plan(self):return self.selected(self.plans)
 def refresh_plans(self):
  rows=list_plans(self.conn);self.fill(self.plans,rows,["plan_id","plan_title","village","record_year","case_title","plan_status","updated_at"])
  self.refresh_allocations()
 def refresh_allocations(self,*args):
  pid=self.selected_plan()
  if pid is None:self.allocations.setRowCount(0);self.plan_flags.setText("Select a plan to review proposed allocation totals.");return
  rows=list_allocations(self.conn,pid);display=[]
  for r in rows:
   share=f"{r['proposed_share_numerator']}/{r['proposed_share_denominator']}" if r["proposed_share_denominator"] else "—"
   display.append({"allocation_id":r["allocation_id"],"khasra_number":r["khasra_number"],"co_sharer_name":r["co_sharer_name"],"proposed_area":r["proposed_area"],"area_unit":r["area_unit"],"share":share,"notes":r["location_or_quality_notes"]})
  self.fill(self.allocations,display,["allocation_id","khasra_number","co_sharer_name","proposed_area","area_unit","share","notes"])
  try:
   plan,results,flags=analyse_plan(self.conn,pid)
   self.plan_flags.setText("Plan checks:\n"+("\n".join("• "+x for x in flags) if flags else "No arithmetic flags generated."))
  except Exception as e:self.plan_flags.setText(str(e))
 def new_plan(self):
  sets=[(f"{r['village']} — {r['record_year']} [{r['record_type']}]",r["record_set_id"]) for r in record_sets(self.conn)]
  if not sets:QMessageBox.information(self,"No source records","Add a source record set first.");return
  cases=[("Not linked",None)]+[(f"#{r['case_id']} — {r['case_title']}",r["case_id"]) for r in list_cases(self.conn)]
  d=PartitionForm("New partition working plan",[("plan_title","Plan title","text",""),("record_set_id","Source record set","text",""),("case_id","Related case","text",""),("plan_status","Status","text","Working"),("basis_notes","Basis / source notes","multi",""),("assumptions","Assumptions and constraints","multi","")],self,{"record_set_id":sets,"case_id":cases,"plan_status":[(x,x) for x in PLAN_STATUSES]})
  if d.exec():
   try:create_plan(self.conn,d.values());self.refresh_plans()
   except Exception as e:QMessageBox.warning(self,"Could not create plan",str(e))
 def edit_plan(self):
  pid=self.selected_plan()
  if pid is None:return
  r=get_plan(self.conn,pid)
  d=PartitionForm("Edit partition plan",[("plan_title","Plan title","text",r["plan_title"]),("plan_status","Status","text",r["plan_status"]),("basis_notes","Basis / source notes","multi",r["basis_notes"]),("assumptions","Assumptions and constraints","multi",r["assumptions"])],self,{"plan_status":[(x,x) for x in PLAN_STATUSES]})
  if d.exec():
   try:update_plan(self.conn,pid,d.values());self.refresh_plans()
   except Exception as e:QMessageBox.warning(self,"Could not update plan",str(e))
 def remove_plan(self):
  pid=self.selected_plan()
  if pid is None:return
  if QMessageBox.question(self,"Delete plan","Delete this plan and its proposed allocations? Source records and case data are retained.")==QMessageBox.Yes:
   delete_plan(self.conn,pid);self.refresh_plans()
 def new_allocation(self):
  pid=self.selected_plan()
  if pid is None:QMessageBox.information(self,"Select plan","Create or select a partition plan first.");return
  plan=get_plan(self.conn,pid)
  owners=self.conn.execute("SELECT DISTINCT owner_name FROM revenue_record_entries WHERE record_set_id=? ORDER BY owner_name",(plan["record_set_id"],)).fetchall()
  khasras=self.conn.execute("SELECT DISTINCT khasra_number FROM revenue_record_entries WHERE record_set_id=? ORDER BY khasra_number",(plan["record_set_id"],)).fetchall()
  d=PartitionForm("Add proposed Khasra allocation",[("khasra_number","Khasra number","text",""),("co_sharer_name","Co-sharer","text",""),("proposed_area","Proposed area (numeric)","text","0"),("area_unit","Area unit","text","acre"),("proposed_share_numerator","Proposed share numerator (optional)","text",""),("proposed_share_denominator","Proposed share denominator (optional)","text",""),("location_or_quality_notes","Location, access, quality, irrigation or other notes","multi","")],self,{"khasra_number":[(r["khasra_number"],r["khasra_number"]) for r in khasras],"co_sharer_name":[(r["owner_name"],r["owner_name"]) for r in owners],"area_unit":[(x,x) for x in ["acre","kanal","marla","sq_yard","hectare","sq_metre"]]})
  if d.exec():
   v=d.values()
   try:
    v["proposed_area"]=float(v["proposed_area"])
    for k in ["proposed_share_numerator","proposed_share_denominator"]:v[k]=int(v[k]) if v[k] else None
    add_allocation(self.conn,pid,v);self.refresh_allocations()
   except Exception as e:QMessageBox.warning(self,"Invalid allocation",str(e))
 def remove_allocation(self):
  aid=self.selected(self.allocations)
  if aid is None:return
  delete_allocation(self.conn,aid);self.refresh_allocations()
 def export_report(self):
  pid=self.selected_plan()
  if pid is None:return
  path,_=QFileDialog.getSaveFileName(self,"Export partition working statement",f"partition-plan-{pid}.txt","Text files (*.txt)")
  if not path:return
  try:
   Path(path).write_text(build_partition_report(self.conn,pid),encoding="utf-8")
   QMessageBox.information(self,"Export complete",f"Saved to:\n{path}")
  except Exception as e:QMessageBox.warning(self,"Export failed",str(e))
