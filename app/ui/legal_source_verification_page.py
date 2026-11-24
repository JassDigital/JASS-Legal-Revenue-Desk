from pathlib import Path
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QComboBox,QTableWidget,
 QTableWidgetItem,QHeaderView,QAbstractItemView,QDialog,QFormLayout,QTextEdit,QDialogButtonBox,QMessageBox,
 QFileDialog,QTabWidget)
from app.services.legal_source_verification import *

class EntryDialog(QDialog):
 def __init__(self,title,fields,parent=None,choices=None):
  super().__init__(parent);self.setWindowTitle(title);self.widgets={};layout=QVBoxLayout(self);form=QFormLayout()
  for key,label,kind,default in fields:
   if choices and key in choices:
    w=QComboBox()
    for text,value in choices[key]:w.addItem(text,value)
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

class LegalSourceVerificationPage(QWidget):
 def __init__(self,conn):
  super().__init__();self.conn=conn;root=QVBoxLayout(self)
  h=QLabel("Legal Source Verification & Citation Engine");h.setObjectName("pageTitle");root.addWidget(h)
  note=QLabel("Preserve source identity, provenance, effective-date history and pinpoint citations. A recorded URL, official host or hash does not by itself prove authenticity, commencement or current legal force.")
  note.setWordWrap(True);note.setObjectName("muted");root.addWidget(note)
  self.summary=QLabel();root.addWidget(self.summary)
  bar=QHBoxLayout();self.query=QLineEdit();self.query.setPlaceholderText("Search title, publisher, identifier or URL");self.query.returnPressed.connect(self.refresh);bar.addWidget(self.query,1)
  self.status=QComboBox();self.status.addItems(["All"]+VERIFICATION_STATES);self.status.currentTextChanged.connect(self.refresh);bar.addWidget(self.status)
  for label,fn in [("New source record",self.new_source),("Edit",self.edit_source),("Delete",self.remove_source),("Preserve & hash snapshot",self.hash_snapshot),("Export dossier",self.export_report)]:
   b=QPushButton(label);b.clicked.connect(fn);bar.addWidget(b)
  root.addLayout(bar)
  self.source_table=self.table(["ID","Source title","Type","Publisher","Jurisdiction","Publication","Effective from","Legal status","Verification"])
  self.source_table.itemSelectionChanged.connect(self.refresh_details);root.addWidget(self.source_table,2)
  self.tabs=QTabWidget();root.addWidget(self.tabs,2)
  self.version_table=self.table(["ID","Version / instrument","Effective from","Effective to","Publication","Verification","Change summary"])
  self.citation_table=self.table(["ID","Target","Kind","Pinpoint","Proposition","Verification"])
  for table,buttons in [(self.version_table,[("Add version",self.new_version)]),(self.citation_table,[("Add citation link",self.new_citation),("Delete selected",self.remove_citation)])]:
   page=QWidget();l=QVBoxLayout(page);row=QHBoxLayout()
   for label,fn in buttons:
    b=QPushButton(label);b.clicked.connect(fn);row.addWidget(b)
   row.addStretch(1);l.addLayout(row);l.addWidget(table,1);self.tabs.addTab(page,"Version History" if table is self.version_table else "Citation Links")
  self.refresh()
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
 def sid(self):return self.selected(self.source_table)
 def refresh(self,*args):
  rows=source_records(self.conn,self.query.text(),self.status.currentText())
  self.fill(self.source_table,rows,["source_record_id","source_title","source_type","publisher","jurisdiction","publication_date","effective_from","legal_status","verification_status"])
  c=dashboard_counts(self.conn);self.summary.setText(f"Source records: {c['total'] or 0}   |   Unverified: {c['unverified'] or 0}   |   Disputed: {c['disputed'] or 0}   |   Legal status uncertain/unverified: {c['status_uncertain'] or 0}")
  self.refresh_details()
 def refresh_details(self):
  sid=self.sid()
  if sid is None:self.version_table.setRowCount(0);self.citation_table.setRowCount(0);return
  self.fill(self.version_table,source_versions(self.conn,sid),["source_version_id","version_label","effective_from","effective_to","publication_date","verification_status","change_summary"])
  self.fill(self.citation_table,citations(self.conn,sid),["citation_link_id","target_label","citation_kind","pinpoint","proposition","verification_status"])
 def source_fields(self,r=None):
  def val(k):return r[k] if r else ""
  return [
   ("source_title","Source title","text",val("source_title")),("source_type","Source type","text",val("source_type") or "Other"),
   ("publisher","Publisher / issuing authority","text",val("publisher")),("jurisdiction","Jurisdiction / territory","text",val("jurisdiction") or "Haryana"),
   ("source_url","Exact source URL","text",val("source_url")),("source_identifier","Gazette number / Act number / case citation","text",val("source_identifier")),
   ("publication_date","Publication date YYYY-MM-DD","text",val("publication_date")),("retrieval_date","Retrieval date YYYY-MM-DD","text",val("retrieval_date")),
   ("effective_from","Effective from YYYY-MM-DD","text",val("effective_from")),("effective_to","Effective to YYYY-MM-DD","text",val("effective_to")),
   ("material_id","Linked revenue material ID (optional)","text",val("material_id")),("section_id","Linked revenue section ID (optional)","text",val("section_id")),
   ("judgment_id","Linked judgment ID (optional)","text",val("judgment_id")),("document_id","Linked library document ID (optional)","text",val("document_id")),
   ("officiality","Source classification","text",val("officiality") or "unknown"),("legal_status","Legal status review","text",val("legal_status") or "unverified"),
   ("verification_status","Verification status","text",val("verification_status") or "unverified"),("verified_by","Reviewed by","text",val("verified_by")),
   ("verified_date","Review date YYYY-MM-DD","text",val("verified_date")),("hash_sha256","SHA-256 (optional)","text",val("hash_sha256")),
   ("source_snapshot_path","Preserved snapshot path","text",val("source_snapshot_path")),("verification_notes","Verification notes / limitations","multi",val("verification_notes"))]
 def new_source(self):
  d=EntryDialog("Register legal source",self.source_fields(),self,{"source_type":[(x,x) for x in SOURCE_TYPES],"officiality":[(x,x) for x in OFFICIALITY],"legal_status":[(x,x) for x in LEGAL_STATES],"verification_status":[(x,x) for x in VERIFICATION_STATES]})
  if d.exec():
   try:
    v=d.values()
    for k in ["material_id","section_id","judgment_id","document_id"]:v[k]=int(v[k]) if v[k] else None
    save_source(self.conn,v);self.refresh()
   except Exception as e:QMessageBox.warning(self,"Could not save",str(e))
 def edit_source(self):
  sid=self.sid()
  if sid is None:return
  r=get_source(self.conn,sid);d=EntryDialog("Edit legal source",self.source_fields(r),self,{"source_type":[(x,x) for x in SOURCE_TYPES],"officiality":[(x,x) for x in OFFICIALITY],"legal_status":[(x,x) for x in LEGAL_STATES],"verification_status":[(x,x) for x in VERIFICATION_STATES]})
  if d.exec():
   try:
    v=d.values()
    for k in ["material_id","section_id","judgment_id","document_id"]:v[k]=int(v[k]) if v[k] else None
    save_source(self.conn,v,sid);self.refresh()
   except Exception as e:QMessageBox.warning(self,"Could not update",str(e))
 def remove_source(self):
  sid=self.sid()
  if sid and QMessageBox.question(self,"Delete source","Delete this source record, its version history and citation links?") == QMessageBox.Yes:
   delete_source(self.conn,sid);self.refresh()
 def hash_snapshot(self):
  sid=self.sid()
  if not sid:return
  path,_=QFileDialog.getOpenFileName(self,"Select preserved source snapshot")
  if not path:return
  try:
   digest=verify_snapshot(self.conn,sid,path);self.refresh();QMessageBox.information(self,"Snapshot preserved",f"SHA-256:\n{digest}\n\nA copy is stored in the application data folder. The hash identifies file bytes; it does not certify authenticity.")
  except Exception as e:QMessageBox.warning(self,"Hash failed",str(e))
 def new_version(self):
  sid=self.sid()
  if not sid:return
  d=EntryDialog("Add version / amendment history",[("version_label","Version label","text",""),("instrument_reference","Amending instrument reference","text",""),("effective_from","Effective from YYYY-MM-DD","text",""),("effective_to","Effective to YYYY-MM-DD","text",""),("publication_date","Publication date YYYY-MM-DD","text",""),("source_reference","Exact source / Gazette reference","multi",""),("change_summary","Change summary","multi",""),("verification_status","Verification status","text","unverified"),("notes","Notes","multi","")],self,{"verification_status":[(x,x) for x in VERIFICATION_STATES]})
  if d.exec():
   try:add_source_version(self.conn,sid,d.values());self.refresh_details()
   except Exception as e:QMessageBox.warning(self,"Could not add version",str(e))
 def new_citation(self):
  sid=self.sid()
  if not sid:return
  d=EntryDialog("Link source to legal proposition",[("target_type","Target type","text","Other"),("target_id","Target record ID (optional)","text",""),("target_label","Target label / case / draft title","text",""),("citation_kind","Relationship","text","Supports"),("pinpoint","Pinpoint: section / paragraph / page","text",""),("proposition","Legal proposition or issue linked","multi",""),("excerpt","Short exact excerpt (optional)","multi",""),("verification_status","Verification status","text","unverified"),("notes","Notes","multi","")],self,{"target_type":[(x,x) for x in TARGET_TYPES],"citation_kind":[(x,x) for x in CITATION_KINDS],"verification_status":[(x,x) for x in VERIFICATION_STATES]})
  if d.exec():
   try:
    v=d.values();v["target_id"]=int(v["target_id"]) if v["target_id"] else None;add_citation(self.conn,sid,v);self.refresh_details()
   except Exception as e:QMessageBox.warning(self,"Could not add citation",str(e))
 def remove_citation(self):
  cid=self.selected(self.citation_table)
  if cid is not None:delete_citation(self.conn,cid);self.refresh_details()
 def export_report(self):
  sid=self.sid()
  if not sid:return
  path,_=QFileDialog.getSaveFileName(self,"Export source dossier",f"legal-source-{sid}.txt","Text files (*.txt)")
  if path:
   try:Path(path).write_text(build_source_report(self.conn,sid),encoding="utf-8");QMessageBox.information(self,"Exported",f"Saved to:\n{path}")
   except Exception as e:QMessageBox.warning(self,"Export failed",str(e))
