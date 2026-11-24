from pathlib import Path
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QLineEdit,
 QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView,QTabWidget,QDialog,QFormLayout,QDialogButtonBox,
 QTextEdit,QMessageBox,QFileDialog)
from app.services.revenue_case_service import list_cases
from app.services.revenue_records_service import record_sets
from app.services.ownership_evidence_workspace import (list_villages,ownership_history,mutation_history,
 compare_ownership_years,evidence_trace,list_review_items,add_review_item,update_review_item,
 delete_review_item,build_ownership_history_report)

class ReviewDialog(QDialog):
 def __init__(self,values=None,parent=None):
  super().__init__(parent);self.setWindowTitle("Ownership evidence review item");v=values or {}
  layout=QVBoxLayout(self);form=QFormLayout();self.kind=QComboBox();self.kind.addItems(["Discrepancy","Ownership claim","Mutation trace","Missing record","Name variation","Share / area issue","Other"]);self.kind.setCurrentText(v.get("review_type","Discrepancy"))
  self.observation=QTextEdit();self.observation.setPlainText(v.get("observation",""))
  self.question=QTextEdit();self.question.setPlainText(v.get("question_for_review",""))
  self.pages=QLineEdit(v.get("page_reference",""))
  self.status=QComboBox();self.status.addItems(["Open","Under review","Resolved","Not pursued"]);self.status.setCurrentText(v.get("review_status","Open"))
  self.verify=QComboBox();self.verify.addItems(["unverified","identity_checked","copy_compared","verified","disputed","needs_review"]);self.verify.setCurrentText(v.get("verification_status","unverified"))
  self.resolution=QTextEdit();self.resolution.setPlainText(v.get("resolution_note",""))
  for label,w in [("Review type",self.kind),("Observation / discrepancy",self.observation),("Question to investigate",self.question),("Source page / paragraph",self.pages),("Review status",self.status),("Verification status",self.verify),("Resolution note",self.resolution)]:
   form.addRow(label,w)
  layout.addLayout(form);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
 def values(self):
  return {"review_type":self.kind.currentText(),"observation":self.observation.toPlainText().strip(),"question_for_review":self.question.toPlainText().strip(),"page_reference":self.pages.text().strip(),"review_status":self.status.currentText(),"verification_status":self.verify.currentText(),"resolution_note":self.resolution.toPlainText().strip()}

class OwnershipEvidenceWorkspacePage(QWidget):
 def __init__(self,conn):
  super().__init__();self.conn=conn;root=QVBoxLayout(self)
  title=QLabel("Land Record Comparison & Ownership Evidence Workspace");title.setObjectName("pageTitle");root.addWidget(title)
  note=QLabel("Trace registered ownership entries across record years, inspect linked mutation records, compare two snapshots and record unresolved evidence questions. This is a research aid, not a title determination.")
  note.setWordWrap(True);note.setObjectName("muted");root.addWidget(note)
  bar=QHBoxLayout();bar.addWidget(QLabel("Case filter"));self.case=QComboBox();self.case.addItem("All cases",None)
  for r in list_cases(conn):self.case.addItem(f"#{r['case_id']} — {r['case_title']}",r["case_id"])
  self.case.currentIndexChanged.connect(self.refresh_all);bar.addWidget(self.case,2)
  bar.addWidget(QLabel("Village"));self.village=QComboBox();self.village.currentIndexChanged.connect(self.refresh_history);bar.addWidget(self.village,2)
  bar.addWidget(QLabel("Khasra"));self.khasra=QLineEdit();self.khasra.setPlaceholderText("Optional exact Khasra");self.khasra.returnPressed.connect(self.refresh_history);bar.addWidget(self.khasra)
  b=QPushButton("Refresh");b.clicked.connect(self.refresh_all);bar.addWidget(b);root.addLayout(bar)
  self.tabs=QTabWidget();root.addWidget(self.tabs,1)
  page=QWidget();lay=QVBoxLayout(page);self.history=self._table(["Year","Set ID","Khasra","Owner","Parent","Khewat","Khata","Khatauni","Area","Share","Record verification","Source document"]);lay.addWidget(self.history);self.tabs.addTab(page,"Ownership History")
  page=QWidget();lay=QVBoxLayout(page);row=QHBoxLayout();self.left=QComboBox();self.right=QComboBox();row.addWidget(QLabel("Earlier snapshot"));row.addWidget(self.left,2);row.addWidget(QLabel("Later snapshot"));row.addWidget(self.right,2);b=QPushButton("Compare snapshots");b.clicked.connect(self.compare);row.addWidget(b);lay.addLayout(row);self.comparison=self._table(["Khasra","Owner","Earlier rows","Later rows","Comparison"]);lay.addWidget(self.comparison);self.compare_note=QLabel("Choose two snapshots for the selected village.");self.compare_note.setWordWrap(True);lay.addWidget(self.compare_note);self.tabs.addTab(page,"Year Comparison")
  page=QWidget();lay=QVBoxLayout(page);self.mutations=self._table(["Date","Mutation No.","Type","Khasra","From","To","Area","Status","Source"]);lay.addWidget(self.mutations);self.tabs.addTab(page,"Mutation History")
  page=QWidget();lay=QVBoxLayout(page);self.sources=self._table(["Year","Record set","Source document","Filename","Record reference","Record verification","Case link","Page","Link verification"]);lay.addWidget(self.sources);self.tabs.addTab(page,"Source Trace")
  page=QWidget();lay=QVBoxLayout(page);buttons=QHBoxLayout()
  for label,fn in [("Add review item",self.add_review),("Edit selected",self.edit_review),("Delete selected",self.delete_review)]:
   b=QPushButton(label);b.clicked.connect(fn);buttons.addWidget(b)
  buttons.addStretch(1);lay.addLayout(buttons);self.reviews=self._table(["ID","Khasra","Owner","Type","Observation","Question","Source document","Page","Status","Verification","Resolution"]);lay.addWidget(self.reviews);self.tabs.addTab(page,"Discrepancy Register")
  b=QPushButton("Export ownership history & evidence report (.txt)");b.clicked.connect(self.export_report);root.addWidget(b)
  self.refresh_all()
 def _table(self,headers):
  t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);t.horizontalHeader().setStretchLastSection(True);t.setSelectionBehavior(QAbstractItemView.SelectRows);t.setEditTriggers(QAbstractItemView.NoEditTriggers);t.setAlternatingRowColors(True);return t
 def _fill(self,table,rows,keys):
  table.setRowCount(len(rows))
  for i,r in enumerate(rows):
   for j,k in enumerate(keys):
    v=r[k] if k in r.keys() else ""
    table.setItem(i,j,QTableWidgetItem("" if v is None else str(v)))
 def case_id(self):return self.case.currentData()
 def refresh_all(self,*args):
  old=self.village.currentData();self.village.blockSignals(True);self.village.clear()
  for r in list_villages(self.conn,self.case_id()):
   self.village.addItem(f"{r['village']} — {r['tehsil'] or ''}, {r['district'] or ''}",r["village"])
  idx=self.village.findData(old)
  if idx>=0:self.village.setCurrentIndex(idx)
  self.village.blockSignals(False);self.refresh_history()
 def refresh_history(self,*args):
  village=self.village.currentData()
  if not village:
   for t in [self.history,self.comparison,self.mutations,self.sources,self.reviews]:t.setRowCount(0)
   self.left.clear();self.right.clear();return
  rows=ownership_history(self.conn,village,self.case_id(),self.khasra.text().strip() or None)
  self._fill(self.history,rows,["record_year","record_set_id","khasra_number","owner_name","parent_name","khewat_number","khata_number","khatauni_number","area_value","share_numerator","set_verification","source_document_id"])
  muts=mutation_history(self.conn,village,self.case_id(),self.khasra.text().strip() or None)
  self._fill(self.mutations,muts,["mutation_date","mutation_number","mutation_type","khasra_numbers","from_party","to_party","area_value","status","source_reference"])
  self._fill(self.sources,evidence_trace(self.conn,village,self.case_id()),["record_year","record_set_id","document_title","original_filename","source_reference","record_verification","case_title","page_reference","link_verification"])
  self.refresh_snapshot_choices();self.refresh_reviews()
 def refresh_snapshot_choices(self):
  village=self.village.currentData();sets=[r for r in record_sets(self.conn) if village and r["village"].casefold()==village.casefold() and (self.case_id() is None or r["case_id"]==self.case_id())]
  for cb in [self.left,self.right]:
   old=cb.currentData();cb.blockSignals(True);cb.clear()
   for r in sets:cb.addItem(f"{r['record_year']} — #{r['record_set_id']} ({r['record_type']})",r["record_set_id"])
   ix=cb.findData(old)
   if ix>=0:cb.setCurrentIndex(ix)
   cb.blockSignals(False)
  if len(sets)>=2 and self.left.currentIndex()==self.right.currentIndex():self.right.setCurrentIndex(1)
 def compare(self):
  if self.left.currentData() is None or self.right.currentData() is None or self.left.currentData()==self.right.currentData():
   QMessageBox.information(self,"Choose snapshots","Choose two different record snapshots.");return
  try:
   a,b,rows=compare_ownership_years(self.conn,self.village.currentData(),self.left.currentData(),self.right.currentData())
   self._fill(self.comparison,rows,["khasra","owner","earlier_rows","later_rows","status"])
   self.compare_note.setText(f"Comparing {a['record_year']} with {b['record_year']}. Matching is by normalized Khasra and owner name; review name variations and duplicate rows.")
  except Exception as e:QMessageBox.warning(self,"Comparison failed",str(e))
 def refresh_reviews(self):
  cid=self.case_id()
  if cid is None:self.reviews.setRowCount(0);return
  self._fill(self.reviews,list_review_items(self.conn,cid),["review_item_id","khasra_number","owner_name","review_type","observation","question_for_review","document_title","page_reference","review_status","verification_status","resolution_note"])
 def selected_review_id(self):
  row=self.reviews.currentRow()
  return int(self.reviews.item(row,0).text()) if row>=0 and self.reviews.item(row,0) else None
 def add_review(self):
  cid=self.case_id()
  if cid is None:QMessageBox.information(self,"Select case","Choose a case before recording a case discrepancy.");return
  d=ReviewDialog(parent=self)
  if d.exec():
   v=d.values();v.update({"village":self.village.currentData() or "","khasra_number":self.khasra.text().strip()})
   try:add_review_item(self.conn,cid,v);self.refresh_reviews()
   except Exception as e:QMessageBox.warning(self,"Save failed",str(e))
 def edit_review(self):
  rid=self.selected_review_id()
  if rid is None:return
  row=next((r for r in list_review_items(self.conn,self.case_id()) if r["review_item_id"]==rid),None)
  if row is None:return
  d=ReviewDialog(dict(row),self)
  if d.exec():
   try:update_review_item(self.conn,rid,d.values());self.refresh_reviews()
   except Exception as e:QMessageBox.warning(self,"Update failed",str(e))
 def delete_review(self):
  rid=self.selected_review_id()
  if rid and QMessageBox.question(self,"Delete review item","Delete selected discrepancy/review item?")==QMessageBox.Yes:
   delete_review_item(self.conn,rid);self.refresh_reviews()
 def export_report(self):
  village=self.village.currentData()
  if not village:QMessageBox.information(self,"Select village","Select a village first.");return
  path,_=QFileDialog.getSaveFileName(self,"Export ownership evidence report",f"ownership-{village.replace(' ','-')}.txt","Text files (*.txt)")
  if path:
   try:Path(path).write_text(build_ownership_history_report(self.conn,village,self.case_id(),self.khasra.text().strip() or None),encoding="utf-8");QMessageBox.information(self,"Exported",f"Saved report to:\n{path}")
   except Exception as e:QMessageBox.warning(self,"Export failed",str(e))
