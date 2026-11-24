from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton,QTableWidget,
    QTableWidgetItem,QHeaderView,QTabWidget,QDialog,QFormLayout,QLineEdit,QTextEdit,QDialogButtonBox,
    QMessageBox,QAbstractItemView)
from app.services.revenue_research_workspace import (materials,sections,save_section,annotations,save_annotation,
    amendments,save_amendment,topic_rows,topic_materials,link_topic_material,material_links,save_material_link)

class FieldsDialog(QDialog):
    def __init__(self,title,fields,parent=None):
        super().__init__(parent); self.setWindowTitle(title); self.widgets={}
        layout=QVBoxLayout(self); form=QFormLayout()
        for key,label,multi,default in fields:
            w=QTextEdit() if multi else QLineEdit()
            if multi: w.setMinimumHeight(95); w.setPlainText(default or "")
            else: w.setText(default or "")
            self.widgets[key]=w; form.addRow(label,w)
        layout.addLayout(form)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
    def values(self):
        return {k:(w.toPlainText().strip() if isinstance(w,QTextEdit) else w.text().strip()) for k,w in self.widgets.items()}

class RevenueResearchPage(QWidget):
    def __init__(self,conn):
        super().__init__(); self.conn=conn; self.current_material_id=None
        root=QVBoxLayout(self)
        title=QLabel("Haryana Revenue Research Workspace"); title.setObjectName("pageTitle"); root.addWidget(title)
        intro=QLabel("Work with provision text, personal research notes, amendment timelines and linked legal materials. Only enter text copied from a checked source; the application does not generate or certify statutory wording.")
        intro.setWordWrap(True); intro.setObjectName("muted"); root.addWidget(intro)
        bar=QHBoxLayout(); bar.addWidget(QLabel("Research material:"))
        self.material_combo=QComboBox(); self.material_combo.currentIndexChanged.connect(self.material_changed); bar.addWidget(self.material_combo,1)
        reload_btn=QPushButton("Reload materials"); reload_btn.clicked.connect(self.load_materials); bar.addWidget(reload_btn)
        root.addLayout(bar)
        self.tabs=QTabWidget(); root.addWidget(self.tabs,1)
        self.section_table=self.make_table(["ID","Section","Heading","Effective from","Effective to","Verification"])
        section_page=self.make_tab(self.section_table,"Add section","Edit selected","Refresh",self.add_section,self.edit_section,self.refresh_sections)
        self.section_query=QLineEdit(); self.section_query.setPlaceholderText("Find within this Act's saved sections and provision text...")
        self.section_query.returnPressed.connect(self.refresh_sections)
        section_page.layout().insertWidget(1,self.section_query)
        self.section_detail=QTextEdit(); self.section_detail.setReadOnly(True); self.section_detail.setMaximumHeight(170)
        self.section_detail.setPlaceholderText("Select a section to read its saved text and source reference.")
        section_page.layout().addWidget(self.section_detail)
        self.section_table.itemSelectionChanged.connect(self.show_section_detail)
        self.tabs.addTab(section_page,"Section Reader")
        self.note_table=self.make_table(["ID","Type","Section","Title","Tags","Updated"])
        self.tabs.addTab(self.make_tab(self.note_table,"Add research note",None,"Refresh",self.add_note,None,self.refresh_notes),"Annotations & Notes")
        self.amend_table=self.make_table(["ID","Affected section","Amendment","Effective from","Effective to","Verification"])
        self.tabs.addTab(self.make_tab(self.amend_table,"Record amendment",None,"Refresh",self.add_amendment,None,self.refresh_amendments),"Amendment Timeline")
        self.link_table=self.make_table(["ID","Relationship","Linked material","Verification","Notes"])
        self.tabs.addTab(self.make_tab(self.link_table,"Link legal material",None,"Refresh",self.add_link,None,self.refresh_links),"Legal Connections")
        self.topic_table=self.make_table(["Topic ID","Research topic","Description","Linked materials"])
        self.tabs.addTab(self.make_tab(self.topic_table,"Link current material to topic",None,"Refresh",self.link_topic,None,self.refresh_topics),"Research Topics")
        self.load_materials()
    def make_table(self,headers):
        t=QTableWidget(0,len(headers)); t.setHorizontalHeaderLabels(headers); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers); t.setSelectionBehavior(QAbstractItemView.SelectRows); t.setAlternatingRowColors(True); return t
    def make_tab(self,table,add_label,edit_label,refresh_label,add_fn,edit_fn,refresh_fn):
        page=QWidget(); layout=QVBoxLayout(page); row=QHBoxLayout()
        add=QPushButton(add_label); add.clicked.connect(add_fn); row.addWidget(add)
        if edit_label:
            edit=QPushButton(edit_label); edit.clicked.connect(edit_fn); row.addWidget(edit)
        refresh=QPushButton(refresh_label); refresh.clicked.connect(refresh_fn); row.addWidget(refresh); row.addStretch(1)
        layout.addLayout(row); layout.addWidget(table,1); return page
    def load_materials(self):
        rows=materials(self.conn); previous=self.material_combo.currentData()
        self.material_combo.blockSignals(True); self.material_combo.clear()
        for r in rows:
            self.material_combo.addItem(f"{r['title']} [{r['material_type']}]",r["material_id"])
        index=self.material_combo.findData(previous) if previous else 0
        if index<0:index=0
        self.material_combo.setCurrentIndex(index); self.material_combo.blockSignals(False)
        self.material_changed()
    def material_changed(self,index=None):
        self.current_material_id=self.material_combo.currentData()
        self.refresh_sections(); self.refresh_notes(); self.refresh_amendments(); self.refresh_links()
    def selected_row_id(self,table):
        row=table.currentRow()
        if row<0:return None
        item=table.item(row,0)
        try:return int(item.text())
        except (ValueError,AttributeError):return None
    def fill(self,table,rows,columns):
        table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,key in enumerate(columns):
                value=r[key] if isinstance(key,str) else key(r)
                table.setItem(i,j,QTableWidgetItem("" if value is None else str(value)))
    def refresh_sections(self):
        if self.current_material_id is None:self.section_table.setRowCount(0);return
        rows=sections(self.conn,self.current_material_id)
        self.fill(self.section_table,rows,["section_id","section_number","heading","effective_from","effective_to","verification_status"])
    def show_section_detail(self):
        sid=self.selected_row_id(self.section_table)
        if not sid:
            self.section_detail.clear(); return
        row=self.conn.execute("SELECT * FROM revenue_law_sections WHERE section_id=?",(sid,)).fetchone()
        if row:
            self.section_detail.setPlainText(
                f"{row['section_number']} — {row['heading'] or ''}\\n\\n{row['section_text']}\\n\\n"
                f"Source reference: {row['source_reference'] or 'Not recorded'}\\n"
                f"Effective period: {row['effective_from'] or 'Unknown'} to {row['effective_to'] or 'Current / unknown'}\\n"
                f"Verification: {row['verification_status']}")
    def add_section(self):
        if self.current_material_id is None:return
        d=FieldsDialog("Add provision / section",[("section_number","Section / paragraph number",False,""),("heading","Heading",False,""),("section_text","Text (transcribe from verified source)",True,""),("source_reference","Source page / paragraph",False,""),("effective_from","Effective from YYYY-MM-DD",False,""),("effective_to","Effective to YYYY-MM-DD",False,""),("verification_status","Verification status",False,"unverified")],self)
        if d.exec():
            v=d.values()
            if not v["section_number"]:QMessageBox.warning(self,"Required","Section number is required.");return
            try:save_section(self.conn,self.current_material_id,**v);self.refresh_sections()
            except Exception as e:QMessageBox.warning(self,"Could not save",str(e))
    def edit_section(self):
        sid=self.selected_row_id(self.section_table)
        if not sid:QMessageBox.information(self,"Select a section","Select a section first.");return
        row=self.conn.execute("SELECT * FROM revenue_law_sections WHERE section_id=?",(sid,)).fetchone()
        fields=[("section_number","Section / paragraph number",False,row["section_number"]),("heading","Heading",False,row["heading"]),("section_text","Text",True,row["section_text"]),("source_reference","Source page / paragraph",False,row["source_reference"]),("effective_from","Effective from",False,row["effective_from"]),("effective_to","Effective to",False,row["effective_to"]),("verification_status","Verification status",False,row["verification_status"])]
        d=FieldsDialog("Edit provision / section",fields,self)
        if d.exec():
            try:save_section(self.conn,self.current_material_id,section_id=sid,**d.values());self.refresh_sections()
            except Exception as e:QMessageBox.warning(self,"Could not save",str(e))
    def refresh_notes(self):
        if self.current_material_id is None:self.note_table.setRowCount(0);return
        rows=annotations(self.conn,self.current_material_id)
        self.fill(self.note_table,rows,["annotation_id","annotation_type","section_number","title","tags","updated_at"])
    def add_note(self):
        if self.current_material_id is None:return
        section_options=sections(self.conn,self.current_material_id)
        d=FieldsDialog("Add research annotation",[("annotation_type","Type",False,"Research note"),("section_number","Section number (optional)",False,""),("title","Title",False,""),("content","Research note / analysis",True,""),("tags","Tags",False,"")],self)
        if not d.exec():return
        v=d.values()
        if not v["title"] or not v["content"]:QMessageBox.warning(self,"Required","Title and content are required.");return
        sid=None
        if v["section_number"]:
            found=next((r for r in section_options if r["section_number"]==v["section_number"]),None)
            if not found:QMessageBox.warning(self,"Section not found","Add the section first or leave the section number blank.");return
            sid=found["section_id"]
        try:save_annotation(self.conn,self.current_material_id,sid,v["annotation_type"],v["title"],v["content"],v["tags"]);self.refresh_notes()
        except Exception as e:QMessageBox.warning(self,"Could not save",str(e))
    def refresh_amendments(self):
        if self.current_material_id is None:self.amend_table.setRowCount(0);return
        rows=amendments(self.conn,self.current_material_id)
        self.fill(self.amend_table,rows,["amendment_id","affected_section","amendment_title","effective_from","effective_to","verification_status"])
    def add_amendment(self):
        if self.current_material_id is None:return
        d=FieldsDialog("Record amendment history",[("affected_section","Affected section",False,""),("amendment_title","Amending Act / notification",False,""),("effective_from","Effective from YYYY-MM-DD",False,""),("effective_to","Effective to YYYY-MM-DD (optional)",False,""),("summary","Summary of change",True,""),("source_reference","Gazette / source reference",False,""),("verification_status","Verification status",False,"unverified")],self)
        if not d.exec():return
        v=d.values()
        if not v["affected_section"] or not v["amendment_title"]:QMessageBox.warning(self,"Required","Affected section and amending instrument are required.");return
        try:save_amendment(self.conn,self.current_material_id,v["affected_section"],v["amendment_title"],None,v["effective_from"],v["effective_to"],v["summary"],v["source_reference"],v["verification_status"]);self.refresh_amendments()
        except Exception as e:QMessageBox.warning(self,"Could not save",str(e))
    def refresh_links(self):
        if self.current_material_id is None:self.link_table.setRowCount(0);return
        rows=material_links(self.conn,self.current_material_id)
        self.fill(self.link_table,rows,["link_id","relationship_type","target_title","verification_status","notes"])
    def add_link(self):
        if self.current_material_id is None:return
        others=[r for r in materials(self.conn) if r["material_id"]!=self.current_material_id]
        if not others:QMessageBox.information(self,"No other material","Add another material in the law library first.");return
        choices="; ".join(f"{r['material_id']}={r['title']}" for r in others)
        d=FieldsDialog("Link another legal material",[("target_id","Target material ID (see list below)",False,""),("relationship_type","Relationship",False,"Amends"),("verification_status","Verification status",False,"unverified"),("notes","Notes",True,"")],self)
        d.layout().insertWidget(0,QLabel(choices))
        if not d.exec():return
        v=d.values()
        try:
            target=int(v["target_id"])
            if target==self.current_material_id or target not in [r["material_id"] for r in others]:raise ValueError("Choose a valid target material ID.")
            save_material_link(self.conn,self.current_material_id,target,v["relationship_type"],v["notes"],v["verification_status"]);self.refresh_links()
        except Exception as e:QMessageBox.warning(self,"Could not save",str(e))
    def refresh_topics(self):
        rows=topic_rows(self.conn); self.fill(self.topic_table,rows,["topic_id","topic_name","description","material_count"])
    def link_topic(self):
        if self.current_material_id is None:return
        rows=topic_rows(self.conn)
        d=FieldsDialog("Link current material to a research topic",[("topic_id","Topic ID",False,""),("notes","Research relevance",True,"")],self)
        d.layout().insertWidget(0,QLabel("; ".join(f"{r['topic_id']}={r['topic_name']}" for r in rows)))
        if not d.exec():return
        try:
            topic_id=int(d.values()["topic_id"])
            if topic_id not in [r["topic_id"] for r in rows]:raise ValueError("Select a valid topic ID.")
            link_topic_material(self.conn,topic_id,self.current_material_id,d.values()["notes"]);self.refresh_topics()
        except Exception as e:QMessageBox.warning(self,"Could not link",str(e))
