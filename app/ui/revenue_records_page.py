from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QTableWidget,
 QTableWidgetItem,QHeaderView,QAbstractItemView,QDialog,QFormLayout,QLineEdit,QTextEdit,QDialogButtonBox,
 QMessageBox,QDoubleSpinBox,QSpinBox,QTabWidget)
from app.services.revenue_case_service import list_cases
from app.services.revenue_records_service import (AREA_UNITS,RECORD_TYPES,VERIFICATION,record_sets,add_record_set,
 add_entry,entries,mutations,add_mutation,delete_record_set,compare_record_sets,record_integrity_flags,
 area_in_acres,share_area)

class FormDialog(QDialog):
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

class RevenueRecordsPage(QWidget):
 def __init__(self,conn):
  super().__init__();self.conn=conn;root=QVBoxLayout(self)
  title=QLabel("Revenue Records Intelligence");title.setObjectName("pageTitle");root.addWidget(title)
  intro=QLabel("Register source-based revenue record snapshots, enter owner-wise entries, track mutations, compare years and run arithmetic checks. Differences are review flags, not findings of title or fraud.")
  intro.setWordWrap(True);intro.setObjectName("muted");root.addWidget(intro)
  self.tabs=QTabWidget();root.addWidget(self.tabs,1)
  self.build_register();self.build_entries();self.build_mutations();self.build_compare();self.build_calculator()
  self.refresh_all()
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
 def build_register(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  for text,fn in [("New record set",self.new_record_set),("Delete selected",self.remove_record_set),("Refresh",self.refresh_all)]:
   b=QPushButton(text);b.clicked.connect(fn);bar.addWidget(b)
  bar.addStretch(1);l.addLayout(bar)
  self.sets=self.table(["ID","Type","Year","District","Tehsil","Village","Hadbast","Source reference","Verification","Case"])
  self.sets.itemSelectionChanged.connect(self.refresh_entries);l.addWidget(self.sets,1)
  self.tabs.addTab(page,"Record Sets")
 def build_entries(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  b=QPushButton("Add owner / khasra entry");b.clicked.connect(self.new_entry);bar.addWidget(b)
  b=QPushButton("Run integrity checks");b.clicked.connect(self.check_integrity);bar.addWidget(b);bar.addStretch(1);l.addLayout(bar)
  self.entry_table=self.table(["ID","Year","Khewat","Khata","Khatauni","Khasra","Owner","Parent","Area","Unit","Share"]);l.addWidget(self.entry_table,1)
  self.tabs.addTab(page,"Ownership Entries")
 def build_mutations(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  b=QPushButton("Add mutation record");b.clicked.connect(self.new_mutation);bar.addWidget(b)
  b=QPushButton("Refresh");b.clicked.connect(self.refresh_mutations);bar.addWidget(b);bar.addStretch(1);l.addLayout(bar)
  self.mutation_table=self.table(["ID","Mutation No.","Date","Type","Village","Khasra","From","To","Area","Status","Source"]);l.addWidget(self.mutation_table,1)
  self.tabs.addTab(page,"Mutation History")
 def build_compare(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  self.left=QComboBox();self.right=QComboBox()
  bar.addWidget(QLabel("Earlier record:"));bar.addWidget(self.left,1);bar.addWidget(QLabel("Later record:"));bar.addWidget(self.right,1)
  b=QPushButton("Compare");b.clicked.connect(self.do_compare);bar.addWidget(b);l.addLayout(bar)
  self.compare_table=self.table(["Khasra","Owner","Comparison result","Earlier rows","Later rows"]);l.addWidget(self.compare_table,1)
  self.compare_note=QLabel("Select two record sets for the same village.");self.compare_note.setWordWrap(True);l.addWidget(self.compare_note)
  self.tabs.addTab(page,"Year Comparison")
 def build_calculator(self):
  page=QWidget();l=QVBoxLayout(page);form=QFormLayout()
  self.area=QDoubleSpinBox();self.area.setMaximum(1e9);self.area.setDecimals(6);self.area.setValue(1)
  self.unit=QComboBox();self.unit.addItems(AREA_UNITS)
  self.num=QSpinBox();self.num.setRange(0,1000000);self.num.setValue(1)
  self.den=QSpinBox();self.den.setRange(1,1000000);self.den.setValue(1)
  form.addRow("Area value",self.area);form.addRow("Area unit",self.unit);form.addRow("Share numerator",self.num);form.addRow("Share denominator",self.den)
  l.addLayout(form);b=QPushButton("Calculate");b.clicked.connect(self.calculate);l.addWidget(b)
  self.calc_result=QLabel("Enter an area and share.");self.calc_result.setWordWrap(True);l.addWidget(self.calc_result);l.addStretch(1)
  l.addWidget(QLabel("Conversions use: 1 acre = 8 kanal = 160 marla = 4,840 square yards. Hectare and square-metre conversions use standard metric factors."))
  self.tabs.addTab(page,"Area & Share Calculator")
 def refresh_all(self):
  rows=record_sets(self.conn);self.fill(self.sets,rows,["record_set_id","record_type","record_year","district","tehsil","village","hadbast_number","source_reference","verification_status","case_title"])
  self.refresh_entries();self.refresh_mutations();self.refresh_compare_choices()
 def current_record_set(self):return self.selected(self.sets)
 def refresh_entries(self,*args):
  rid=self.current_record_set()
  self.fill(self.entry_table,entries(self.conn,rid) if rid else [],["entry_id","record_year","khewat_number","khata_number","khatauni_number","khasra_number","owner_name","parent_name","area_value","area_unit","share_numerator"])
  # Show fraction explicitly in share column.
  if rid:
   rows=entries(self.conn,rid)
   for i,r in enumerate(rows):
    share=(f"{r['share_numerator']}/{r['share_denominator']}" if r["share_numerator"] is not None else "Not entered")
    self.entry_table.setItem(i,10,QTableWidgetItem(share))
 def refresh_mutations(self):
  self.fill(self.mutation_table,mutations(self.conn),["mutation_id","mutation_number","mutation_date","mutation_type","village","khasra_numbers","from_party","to_party","area_value","status","source_reference"])
 def refresh_compare_choices(self):
  sets=record_sets(self.conn)
  for cb in [self.left,self.right]:
   old=cb.currentData();cb.blockSignals(True);cb.clear()
   for r in sets:cb.addItem(f"{r['village']} — {r['record_year']} ({r['record_type']}) [#{r['record_set_id']}]",r["record_set_id"])
   idx=cb.findData(old)
   if idx>=0:cb.setCurrentIndex(idx)
   cb.blockSignals(False)
 def new_record_set(self):
  cases=[("No linked case",None)]+[(f"#{r['case_id']} — {r['case_title']}",r["case_id"]) for r in list_cases(self.conn)]
  docs=[("No linked document",None)]+[(f"#{r['document_id']} — {r['document_title']}",r["document_id"]) for r in self.conn.execute("SELECT document_id,document_title FROM documents ORDER BY document_title")]
  choices={"record_type":[(x,x) for x in RECORD_TYPES],"case_id":cases,"source_document_id":docs,"verification_status":[(x,x) for x in VERIFICATION]}
  d=FormDialog("Register revenue record set",[("record_type","Record type","text","Jamabandi"),("record_year","Year / period","text",""),("district","District","text",""),("tehsil","Tehsil","text",""),("village","Village","text",""),("hadbast_number","Hadbast number","text",""),("estate_name","Estate name","text",""),("case_id","Link case","text",""),("source_reference","Source / page reference","text",""),("source_document_id","Link source document","text",""),("verification_status","Source verification","text","unverified"),("notes","Notes","multi","")],self,choices)
  if d.exec():
   try:add_record_set(self.conn,d.values());self.refresh_all()
   except Exception as e:QMessageBox.warning(self,"Could not save",str(e))
 def remove_record_set(self):
  rid=self.current_record_set()
  if rid is None:return
  if QMessageBox.question(self,"Delete record set","Delete this snapshot and its owner entries? Mutation records linked to it will be retained without the link.")==QMessageBox.Yes:
   delete_record_set(self.conn,rid);self.refresh_all()
 def new_entry(self):
  rid=self.current_record_set()
  if rid is None:QMessageBox.information(self,"Select record set","Create or select a record set first.");return
  d=FormDialog("Add Jamabandi / khasra owner entry",[
   ("khewat_number","Khewat number","text",""),("khata_number","Khata number","text",""),("khatauni_number","Khatauni number","text",""),
   ("khasra_number","Khasra number","text",""),("owner_name","Owner name","text",""),("parent_name","Father / spouse name","text",""),
   ("area_value","Area value","text",""),("area_unit","Area unit","text","acre"),("share_numerator","Share numerator (blank if unknown)","text",""),
   ("share_denominator","Share denominator (blank if unknown)","text",""),("entry_notes","Notes","multi","")],self,
   {"area_unit":[(x,x) for x in AREA_UNITS]})
  if d.exec():
   v=d.values()
   try:
    for k in ["area_value","share_numerator","share_denominator"]:v[k]=float(v[k]) if k=="area_value" and v[k] else int(v[k]) if v[k] else None
    add_entry(self.conn,rid,v);self.refresh_entries()
   except Exception as e:QMessageBox.warning(self,"Invalid entry",str(e))
 def new_mutation(self):
  sets=[("Not linked",None)]+[(f"#{r['record_set_id']} — {r['village']} {r['record_year']}",r["record_set_id"]) for r in record_sets(self.conn)]
  cases=[("Not linked",None)]+[(f"#{r['case_id']} — {r['case_title']}",r["case_id"]) for r in list_cases(self.conn)]
  choices={"record_set_id":sets,"case_id":cases,"mutation_type":[(x,x) for x in ["Inheritance","Sale","Gift","Partition","Correction","Court / authority order","Other"]],"status":[(x,x) for x in ["Unverified","Pending","Sanctioned","Rejected","Appealed","Cancelled"]],"area_unit":[(x,x) for x in AREA_UNITS]}
  d=FormDialog("Add mutation history",[("mutation_number","Mutation number","text",""),("mutation_date","Mutation date YYYY-MM-DD","text",""),("mutation_type","Type","text","Other"),("record_set_id","Related record set","text",""),("case_id","Related case","text",""),("khasra_numbers","Khasra numbers","text",""),("from_party","From / predecessor","text",""),("to_party","To / successor","text",""),("area_value","Area value (optional)","text",""),("area_unit","Area unit","text","acre"),("share_numerator","Share numerator (optional)","text",""),("share_denominator","Share denominator (optional)","text",""),("status","Status","text","Unverified"),("source_reference","Source reference","text",""),("notes","Notes","multi","")],self,choices)
  if d.exec():
   v=d.values()
   try:
    for k in ["area_value","share_numerator","share_denominator"]:v[k]=float(v[k]) if k=="area_value" and v[k] else int(v[k]) if v[k] else None
    add_mutation(self.conn,v);self.refresh_mutations()
   except Exception as e:QMessageBox.warning(self,"Invalid mutation",str(e))
 def do_compare(self):
  a=self.left.currentData();b=self.right.currentData()
  if a is None or b is None or a==b:QMessageBox.information(self,"Choose records","Choose two different record sets.");return
  try:
   left,right,rows=compare_record_sets(self.conn,a,b)
   self.fill(self.compare_table,rows,["khasra","owner","status","earlier_count","later_count"])
   self.compare_note.setText(f"{left['village']}: {left['record_year']} compared with {right['record_year']}. Comparison matches entries by Khasra number + owner name (case-insensitive). Duplicate rows are counted, but only the first matching row is used for field differences. Verify spelling, area basis and source pages.")
  except Exception as e:QMessageBox.warning(self,"Comparison unavailable",str(e))
 def check_integrity(self):
  rid=self.current_record_set()
  if rid is None:return
  flags=record_integrity_flags(self.conn,rid)
  QMessageBox.information(self,"Record checks","No automatic flags from the entered data." if not flags else "\n\n".join(flags))
 def calculate(self):
  try:
   acres=area_in_acres(self.area.value(),self.unit.currentText())
   share=share_area(self.area.value(),self.unit.currentText(),self.num.value(),self.den.value())
   self.calc_result.setText(f"Total area: {acres:.6f} acres ({acres*8:.4f} kanal; {acres*160:.2f} marla)\nShare area: {share:.6f} acres ({share*8:.4f} kanal; {share*160:.2f} marla)")
  except Exception as e:QMessageBox.warning(self,"Calculation error",str(e))
