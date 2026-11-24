"""Legal source register, provenance, version history and citation links.

This module records evidence and human review. It does not determine whether a law is in force.
"""
from pathlib import Path
import hashlib
import shutil
from datetime import date

VERIFICATION_STATES=["unverified","source_located","identity_checked","copy_compared","legally_reviewed","disputed","superseded"]
LEGAL_STATES=["unverified","in_force_confirmed","amended","repealed","not_commenced","historical","uncertain","not_applicable"]
OFFICIALITY=["official_primary","official_copy","court_hosted","secondary_copy","commentary","unknown"]
SOURCE_TYPES=["Act","Amending Act","Rules","Regulation","Gazette notification","Circular / instruction","Judgment","Manual","Official portal","Other"]
TARGET_TYPES=["Revenue case","Proceeding","Draft","Preparation step","Research topic","Other"]
CITATION_KINDS=["Supports","Contradicts","Explains","Amends","Repeals","Interprets","Distinguishes","Other"]

def sha256_file(path):
 p=Path(path)
 if not p.is_file():raise FileNotFoundError(str(p))
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def _date(value,label):
 if not value:return None
 try:date.fromisoformat(value)
 except ValueError:raise ValueError(f"{label} must use YYYY-MM-DD.")
 return value

def source_records(conn,query="",status="All"):
 sql="SELECT s.*,m.title AS material_title,sec.section_number,j.case_title AS judgment_title FROM legal_source_records s LEFT JOIN revenue_law_materials m USING(material_id) LEFT JOIN revenue_law_sections sec USING(section_id) LEFT JOIN judgments j USING(judgment_id) WHERE 1=1"
 args=[]
 if query.strip():
  like=f"%{query.strip()}%";sql+=" AND (s.source_title LIKE ? OR s.publisher LIKE ? OR s.source_identifier LIKE ? OR s.source_url LIKE ? OR s.verification_notes LIKE ?)";args += [like]*5
 if status!="All":sql+=" AND s.verification_status=?";args.append(status)
 sql+=" ORDER BY s.updated_at DESC,s.source_record_id DESC"
 return conn.execute(sql,args).fetchall()

def get_source(conn,sid):
 return conn.execute("SELECT * FROM legal_source_records WHERE source_record_id=?",(sid,)).fetchone()

def save_source(conn,v,sid=None):
 title=(v.get("source_title") or "").strip()
 if not title:raise ValueError("Source title is required.")
 for key,label in [("publication_date","Publication date"),("retrieval_date","Retrieval date"),("effective_from","Effective from"),("effective_to","Effective to"),("verified_date","Verified date")]:_date(v.get(key),label)
 material_id=v.get("material_id") or None;section_id=v.get("section_id") or None
 judgment_id=v.get("judgment_id") or None;document_id=v.get("document_id") or None
 fields=[material_id,section_id,judgment_id,document_id,title,v.get("source_type","Other"),v.get("publisher",""),v.get("jurisdiction","Haryana"),v.get("source_url",""),v.get("source_identifier",""),v.get("publication_date") or None,v.get("retrieval_date") or None,v.get("effective_from") or None,v.get("effective_to") or None,v.get("officiality","unknown"),v.get("legal_status","unverified"),v.get("verification_status","unverified"),v.get("verified_by",""),v.get("verified_date") or None,v.get("hash_sha256",""),v.get("source_snapshot_path",""),v.get("verification_notes","")]
 if sid:
  conn.execute("""UPDATE legal_source_records SET material_id=?,section_id=?,judgment_id=?,document_id=?,source_title=?,source_type=?,publisher=?,jurisdiction=?,source_url=?,source_identifier=?,publication_date=?,retrieval_date=?,effective_from=?,effective_to=?,officiality=?,legal_status=?,verification_status=?,verified_by=?,verified_date=?,hash_sha256=?,source_snapshot_path=?,verification_notes=?,updated_at=CURRENT_TIMESTAMP WHERE source_record_id=?""",fields+[sid]);conn.commit();return sid
 cur=conn.execute("""INSERT INTO legal_source_records(material_id,section_id,judgment_id,document_id,source_title,source_type,publisher,jurisdiction,source_url,source_identifier,publication_date,retrieval_date,effective_from,effective_to,officiality,legal_status,verification_status,verified_by,verified_date,hash_sha256,source_snapshot_path,verification_notes) VALUES("""+",".join(["?"]*22)+")",fields)
 conn.commit();return cur.lastrowid

def delete_source(conn,sid):
 conn.execute("DELETE FROM legal_source_records WHERE source_record_id=?",(sid,));conn.commit()

def add_source_version(conn,sid,v):
 label=(v.get("version_label") or "").strip()
 if not label:raise ValueError("Version label is required.")
 for key,name in [("effective_from","Effective from"),("effective_to","Effective to"),("publication_date","Publication date")]:_date(v.get(key),name)
 cur=conn.execute("""INSERT INTO legal_source_versions(source_record_id,version_label,instrument_reference,effective_from,effective_to,publication_date,source_reference,change_summary,verification_status,notes) VALUES(?,?,?,?,?,?,?,?,?,?)""",(sid,label,v.get("instrument_reference",""),v.get("effective_from") or None,v.get("effective_to") or None,v.get("publication_date") or None,v.get("source_reference",""),v.get("change_summary",""),v.get("verification_status","unverified"),v.get("notes","")))
 conn.commit();return cur.lastrowid

def source_versions(conn,sid):
 return conn.execute("SELECT * FROM legal_source_versions WHERE source_record_id=? ORDER BY COALESCE(effective_from,''),source_version_id",(sid,)).fetchall()

def add_citation(conn,sid,v):
 if not (v.get("target_label") or "").strip() and not v.get("target_id"):raise ValueError("Enter a target label or target ID.")
 if not (v.get("proposition") or "").strip():raise ValueError("Record the legal proposition being linked.")
 cur=conn.execute("""INSERT INTO legal_citation_links(source_record_id,target_type,target_id,target_label,citation_kind,pinpoint,proposition,excerpt,verification_status,notes) VALUES(?,?,?,?,?,?,?,?,?,?)""",(sid,v.get("target_type","Other"),v.get("target_id") or None,(v.get("target_label") or "").strip(),v.get("citation_kind","Supports"),v.get("pinpoint",""),v["proposition"].strip(),v.get("excerpt",""),v.get("verification_status","unverified"),v.get("notes","")))
 conn.commit();return cur.lastrowid

def citations(conn,sid):
 return conn.execute("SELECT * FROM legal_citation_links WHERE source_record_id=? ORDER BY citation_link_id DESC",(sid,)).fetchall()

def delete_citation(conn,cid):
 conn.execute("DELETE FROM legal_citation_links WHERE citation_link_id=?",(cid,));conn.commit()

def verify_snapshot(conn,sid,path,destination_dir=None):
 source=Path(path)
 digest=sha256_file(source)
 if destination_dir is None:
  from app.core.paths import data_dir
  destination_dir=data_dir()/"documents"/"legal_sources"
 destination=Path(destination_dir);destination.mkdir(parents=True,exist_ok=True)
 suffix=source.suffix.lower()[:12]
 target=destination/f"{digest}{suffix}"
 if not target.exists():shutil.copy2(source,target)
 conn.execute("UPDATE legal_source_records SET hash_sha256=?,source_snapshot_path=?,updated_at=CURRENT_TIMESTAMP WHERE source_record_id=?",(digest,str(target.resolve()),sid));conn.commit()
 return digest

def dashboard_counts(conn):
 return conn.execute("""SELECT COUNT(*) total,
 SUM(CASE WHEN verification_status='unverified' THEN 1 ELSE 0 END) unverified,
 SUM(CASE WHEN verification_status='disputed' THEN 1 ELSE 0 END) disputed,
 SUM(CASE WHEN legal_status IN ('uncertain','unverified') THEN 1 ELSE 0 END) status_uncertain
 FROM legal_source_records""").fetchone()

def build_source_report(conn,sid):
 s=get_source(conn,sid)
 if not s:raise ValueError("Source record not found.")
 out=["JASS LEGAL & REVENUE DESK — LEGAL SOURCE DOSSIER","="*65,"",f"Source: {s['source_title']}",f"Type: {s['source_type']}",f"Publisher: {s['publisher']}",f"Jurisdiction: {s['jurisdiction']}",f"URL: {s['source_url']}",f"Identifier: {s['source_identifier']}",f"Publication date: {s['publication_date']}",f"Retrieved: {s['retrieval_date']}",f"Effective period entered: {s['effective_from']} to {s['effective_to']}",f"Officiality classification: {s['officiality']}",f"Legal status review: {s['legal_status']}",f"Verification: {s['verification_status']}",f"Reviewer/date: {s['verified_by']} / {s['verified_date']}",f"SHA-256: {s['hash_sha256']}",f"Preserved snapshot: {s['source_snapshot_path']}",f"Notes: {s['verification_notes']}","","VERSION / AMENDMENT HISTORY"]
 for r in source_versions(conn,sid):out.append(f"- {r['version_label']} | {r['instrument_reference']} | effective {r['effective_from']} to {r['effective_to']} | published {r['publication_date']} | {r['verification_status']}\n  Source: {r['source_reference']}\n  Change: {r['change_summary']}\n  Notes: {r['notes']}")
 out += ["","CITATION LINKS"]
 for r in citations(conn,sid):out.append(f"- {r['citation_kind']} → {r['target_type']}: {r['target_label']} (ID {r['target_id'] or 'not linked'})\n  Pinpoint: {r['pinpoint']}\n  Proposition: {r['proposition']}\n  Excerpt: {r['excerpt']}\n  Verification: {r['verification_status']}\n  Notes: {r['notes']}")
 out += ["","IMPORTANT: This dossier is a provenance and research aid. It does not itself establish authenticity, commencement, current force, territorial application, constitutional validity, or binding precedential status. Verify the original official publication, amendments, commencement instruments, repeal/savings provisions, later judicial treatment and relevant effective date before relying on a proposition."]
 return "\n".join(out)
