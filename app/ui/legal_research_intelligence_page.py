from pathlib import Path
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QComboBox,QTableWidget,
 QTableWidgetItem,QHeaderView,QAbstractItemView,QDialog,QFormLayout,QTextEdit,QDialogButtonBox,QMessageBox,
 QFileDialog,QTabWidget)
from app.services.revenue_case_service import list_cases
from app.services.legal_source_verification import VERIFICATION_STATES
from app.services.legal_research_intelligence import *

class ResearchDialog(QDialog):
 def __init__(self,title,fields,parent=None,choices=None):
  super().__init__(parent);self.setWindowTitle(title);self.widgets={};layout=QVBoxLayout(self);form=QFormLayout()
  for key,label,kind,default in fields:
   if choices and key in choices:
    w=QComboBox()
    for text,val in choices[key]:w.addItem(text,val)
    idx=w.findData(default)
    if idx>=0:w.setCurrentIndex(idx)
   elif kind=="multi":w=QTextEdit();w.setMinimumHeight(65);w.setPlainText(default or "")
   else:w=QLineEdit();w.setText("" if default is None else str(default))
   self.widgets[key]=w;form.addRow(label,w)
  layout.addLayout(form);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
  buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
 def values(self):
  from PySide6.QtWidgets import QTextEdit
  return {k:(w.toPlainText().strip() if isinstance(w,QTextEdit) else w.currentData() if isinstance(w,QComboBox) else w.text().strip()) for k,w in self.widgets.items()}

class LegalResearchIntelligencePage(QWidget):
 def __init__(self,conn):
  super().__init__();self.conn=conn;root=QVBoxLayout(self)
  h=QLabel("Haryana Legal Research Intelligence & Case Argument Builder");h.setObjectName("pageTitle");root.addWidget(h)
  note=QLabel("Search your registered source library, organize research by issue, and build arguments with supporting and contrary authorities. Search coverage is limited to sources you have registered.")
  note.setWordWrap(True);note.setObjectName("muted");root.addWidget(note)
  self.tabs=QTabWidget();root.addWidget(self.tabs,1)
  self.build_search_tab();self.build_bundle_tab();self.refresh_cases();self.refresh_sources()
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
 def build_search_tab(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  self.search=QLineEdit();self.search.setPlaceholderText("Search statutory text, section number, judgment text, citation, subject or source metadata");self.search.returnPressed.connect(self.refresh_sources);bar.addWidget(self.search,1)
  self.search_ver=QComboBox();self.search_ver.addItems(["All"]+VERIFICATION_STATES);bar.addWidget(self.search_ver)
  self.search_jur=QComboBox();self.search_jur.addItems(["All","Haryana","Central","Punjab"]);bar.addWidget(self.search_jur)
  b=QPushButton("Search registered sources");b.clicked.connect(self.refresh_sources);bar.addWidget(b);l.addLayout(bar)
  self.source_table=self.table(["Source ID","Source title","Type","Linked section / judgment","Legal status","Verification","Officiality","Publisher"])
  self.source_table.itemSelectionChanged.connect(self.show_source_detail);l.addWidget(self.source_table,1)
  self.source_detail=QTextEdit();self.source_detail.setReadOnly(True);self.source_detail.setMaximumHeight(110);l.addWidget(self.source_detail)
  self.tabs.addTab(page,"Source Search")
 def build_bundle_tab(self):
  page=QWidget();l=QVBoxLayout(page);bar=QHBoxLayout()
  self.case_filter=QComboBox();self.case_filter.addItem("All bundles",None);self.case_filter.currentIndexChanged.connect(self.refresh_bundles);bar.addWidget(self.case_filter,1)
  for label,fn in [("New bundle",self.new_bundle),("Edit bundle",self.edit_bundle),("Delete bundle",self.remove_bundle),("Export bundle",self.export_bundle)]:
   b=QPushButton(label);b.clicked.connect(fn);bar.addWidget(b)
  l.addLayout(bar)
  self.bundle_table=self.table(["ID","Bundle","Case","Status","Research question"]);self.bundle_table.itemSelectionChanged.connect(self.refresh_bundle_detail);l.addWidget(self.bundle_table,1)
  self.bundle_tabs=QTabWidget();l.addWidget(self.bundle_tabs,2)
  issuepage=QWidget();il=QVBoxLayout(issuepage);ib=QHBoxLayout()
  for label,fn in [("Add issue",self.new_issue),("Edit issue",self.edit_issue),("Delete issue",self.remove_issue)]:
   b=QPushButton(label);b.clicked.connect(fn);ib.addWidget(b)
  ib.addStretch(1);il.addLayout(ib);self.issue_table=self.table(["ID","Issue","Legal question","Status"]);self.issue_table.itemSelectionChanged.connect(self.refresh_issue_detail);il.addWidget(self.issue_table,1)
  self.issue_detail=QTextEdit();self.issue_detail.setReadOnly(True);self.issue_detail.setMaximumHeight(95);il.addWidget(self.issue_detail)
  self.bundle_tabs.addTab(issuepage,"Issues")
  sourcepage=QWidget();sl=QVBoxLayout(sourcepage);sb=QHBoxLayout()
  for label,fn in [("Attach selected search result",self.attach_selected_source),("Detach selected",self.detach_selected_source)]:
   b=QPushButton(label);b.clicked.connect(fn);sb.addWidget(b)
  sb.addStretch(1);sl.addLayout(sb);self.issue_source_table=self.table(["Link ID","Position","Source","Pinpoint","Source verification","Legal status"]);sl.addWidget(self.issue_source_table,1)
  self.bundle_tabs.addTab(sourcepage,"Issue Sources")
  argpage=QWidget();al=QVBoxLayout(argpage);ab=QHBoxLayout()
  for label,fn in [("Add argument",self.new_argument),("Delete selected",self.remove_argument)]:
   b=QPushButton(label);b.clicked.connect(fn);ab.addWidget(b)
  ab.addStretch(1);al.addLayout(ab);self.argument_table=self.table(["ID","Type","Argument","Status"]);al.addWidget(self.argument_table,1)
  self.bundle_tabs.addTab(argpage,"Arguments")
  l.addWidget(self.bundle_tabs,2);self.tabs.addTab(page,"Research Bundles")
 def refresh_cases(self):
  old=self.case_filter.currentData();self.case_filter.blockSignals(True);self.case_filter.clear();self.case_filter.addItem("All bundles",None)
  for r in list_cases(self.conn):self.case_filter.addItem(f"#{r['case_id']} — {r['case_title']}",r["case_id"])
  idx=self.case_filter.findData(old)
  if idx>=0:self.case_filter.setCurrentIndex(idx)
  self.case_filter.blockSignals(False);self.refresh_bundles()
 def refresh_sources(self,*args):
  rows=search_research_sources(self.conn,self.search.text(),self.search_ver.currentText(),self.search_jur.currentText())
  self.fill(self.source_table,rows,["source_record_id","source_title","source_type","linked_reference","legal_status","verification_status","officiality","publisher"])
  self.search_rows={r["source_record_id"]:r for r in rows};self.show_source_detail()
 def show_source_detail(self):
  sid=self.selected(self.source_table)
  r=get_source(self.conn,sid) if sid else None
  if not r:self.source_detail.clear();return
  self.source_detail.setPlainText("\n".join([f"Source: {r['source_title']}",f"URL: {r['source_url']}",f"Identifier: {r['source_identifier']}",f"Verification: {r['verification_status']} | Legal status: {r['legal_status']} | Officiality: {r['officiality']}",f"Reviewer: {r['verified_by']} / {r['verified_date']}",f"Notes: {r['verification_notes']}"]))
 def refresh_bundles(self,*args):
  rows=bundles(self.conn,self.case_filter.currentData());self.fill(self.bundle_table,rows,["bundle_id","title","case_title","status","research_question"]);self.refresh_bundle_detail()
 def bundle_id(self):return self.selected(self.bundle_table)
 def issue_id(self):return self.selected(self.issue_table)
 def refresh_bundle_detail(self):
  bid=self.bundle_id()
  if not bid:
   self.issue_table.setRowCount(0);self.issue_source_table.setRowCount(0);self.argument_table.setRowCount(0);self.issue_detail.clear();return
  self.fill(self.issue_table,bundle_issues(self.conn,bid),["research_issue_id","issue_title","legal_question","issue_status"]);self.refresh_issue_detail()
 def refresh_issue_detail(self):
  iid=self.issue_id()
  if not iid:
   self.issue_source_table.setRowCount(0);self.argument_table.setRowCount(0);self.issue_detail.clear();return
  issue=next((x for x in bundle_issues(self.conn,self.bundle_id()) if x["research_issue_id"]==iid),None)
  if issue:self.issue_detail.setPlainText(f"Facts: {issue['material_facts']}\nQuestion: {issue['legal_question']}\nProvisional view: {issue['provisional_view']}")
  self.fill(self.issue_source_table,issue_sources(self.conn,iid),["issue_source_id","position","source_title","pinpoint","source_verification","legal_status"])
  self.fill(self.argument_table,arguments(self.conn,iid),["argument_id","argument_type","argument_text","status"])
 def new_bundle(self):
  cases=[("General research (not linked to a case)",None)]+[(f"#{r['case_id']} — {r['case_title']}",r["case_id"]) for r in list_cases(self.conn)]
  d=ResearchDialog("Create research bundle",[("title","Bundle title","text",""),("research_question","Research question","multi",""),("scope_notes","Scope / jurisdiction / date limits","multi",""),("status","Status","text","Working")],self,{"status":[(x,x) for x in ["Working","For review","Ready for use","Archived"]]})
  if d.exec():
   try:
    v=d.values();v["case_id"]=self.case_filter.currentData();create_bundle(self.conn,v);self.refresh_bundles()
   except Exception as e:QMessageBox.warning(self,"Could not create bundle",str(e))
 def edit_bundle(self):
  bid=self.bundle_id()
  if not bid:return
  r=next((x for x in bundles(self.conn) if x["bundle_id"]==bid),None)
  if not r:return
  d=ResearchDialog("Edit research bundle",[("title","Bundle title","text",r["title"]),("research_question","Research question","multi",r["research_question"]),("scope_notes","Scope / jurisdiction / date limits","multi",r["scope_notes"]),("status","Status","text",r["status"])],self,{"status":[(x,x) for x in ["Working","For review","Ready for use","Archived"]]})
  if d.exec():
   try:update_bundle(self.conn,bid,d.values());self.refresh_bundles()
   except Exception as e:QMessageBox.warning(self,"Could not update",str(e))
 def remove_bundle(self):
  bid=self.bundle_id()
  if bid and QMessageBox.question(self,"Delete bundle","Delete bundle, issues, arguments and source links? Registered source records remain.")==QMessageBox.Yes:delete_bundle(self.conn,bid);self.refresh_bundles()
 def new_issue(self):
  bid=self.bundle_id()
  if not bid:return
  d=ResearchDialog("Add research issue",[("issue_title","Issue title","text",""),("material_facts","Material facts","multi",""),("legal_question","Legal question","multi",""),("provisional_view","Provisional view / uncertainty","multi",""),("issue_status","Status","text","Open")],self,{"issue_status":[(x,x) for x in ["Open","Researching","For review","Resolved","Deferred"]]})
  if d.exec():
   try:create_issue(self.conn,bid,d.values());self.refresh_bundle_detail()
   except Exception as e:QMessageBox.warning(self,"Could not add issue",str(e))
 def edit_issue(self):
  iid=self.issue_id()
  if not iid:return
  r=next((x for x in bundle_issues(self.conn,self.bundle_id()) if x["research_issue_id"]==iid),None)
  if not r:return
  d=ResearchDialog("Edit research issue",[("issue_title","Issue title","text",r["issue_title"]),("material_facts","Material facts","multi",r["material_facts"]),("legal_question","Legal question","multi",r["legal_question"]),("provisional_view","Provisional view / uncertainty","multi",r["provisional_view"]),("issue_status","Status","text",r["issue_status"])],self,{"issue_status":[(x,x) for x in ["Open","Researching","For review","Resolved","Deferred"]]})
  if d.exec():
   try:update_issue(self.conn,iid,d.values());self.refresh_bundle_detail()
   except Exception as e:QMessageBox.warning(self,"Could not update issue",str(e))
 def remove_issue(self):
  iid=self.issue_id()
  if iid and QMessageBox.question(self,"Delete issue","Delete issue, arguments and source links?") == QMessageBox.Yes:delete_issue(self.conn,iid);self.refresh_bundle_detail()
 def attach_selected_source(self):
  iid=self.issue_id();sid=self.selected(self.source_table)
  if not iid or not sid:QMessageBox.information(self,"Select records","Select an issue and a source result in Source Search first.");return
  d=ResearchDialog("Attach source to issue",[("position","Position","text","Relevant"),("pinpoint","Pinpoint section / paragraph / page","text",""),("proposition","Proposition linked to this issue","multi",""),("relevance_note","Relevance / treatment note","multi",""),("verification_status","Link verification","text","unverified")],self,{"position":[(x,x) for x in POSITIONS],"verification_status":[(x,x) for x in VERIFICATION_STATES]})
  if d.exec():
   try:attach_source(self.conn,iid,sid,d.values());self.refresh_issue_detail()
   except Exception as e:QMessageBox.warning(self,"Could not attach source",str(e))
 def detach_selected_source(self):
  xid=self.selected(self.issue_source_table)
  if xid:detach_source(self.conn,xid);self.refresh_issue_detail()
 def new_argument(self):
  iid=self.issue_id()
  if not iid:return
  d=ResearchDialog("Add issue argument",[("argument_type","Argument type","text","Proposed"),("argument_text","Argument / analysis","multi",""),("status","Status","text","Draft"),("notes","Notes / gaps / counterpoints","multi","")],self,{"argument_type":[(x,x) for x in ARGUMENT_TYPES],"status":[(x,x) for x in ["Draft","Needs research","For review","Approved for draft","Not pursued"]]})
  if d.exec():
   try:add_argument(self.conn,iid,d.values());self.refresh_issue_detail()
   except Exception as e:QMessageBox.warning(self,"Could not add argument",str(e))
 def remove_argument(self):
  aid=self.selected(self.argument_table)
  if aid:delete_argument(self.conn,aid);self.refresh_issue_detail()
 def export_bundle(self):
  bid=self.bundle_id()
  if not bid:return
  path,_=QFileDialog.getSaveFileName(self,"Export legal research bundle",f"legal-research-bundle-{bid}.txt","Text files (*.txt)")
  if path:
   try:Path(path).write_text(build_bundle_report(self.conn,bid),encoding="utf-8");QMessageBox.information(self,"Exported",f"Saved to:\n{path}")
   except Exception as e:QMessageBox.warning(self,"Export failed",str(e))
