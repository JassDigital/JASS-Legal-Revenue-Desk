"""Case-linked document discovery, metadata and evidence indexing."""
import re

LINK_TYPES=["Evidence","Ownership record","Mutation order","Revenue order","Application / pleading","Correspondence","Map / site plan","Other"]
VERIFY_STATES=["unverified","identity_checked","copy_compared","verified","needs_review"]

def search_documents(conn,query="",document_type="All",case_id=None,limit=500):
    query=(query or "").strip()
    args=[];where=[]
    if document_type and document_type!="All":where.append("d.document_type=?");args.append(document_type)
    if case_id is not None:
        where.append("EXISTS(SELECT 1 FROM revenue_case_document_links l WHERE l.document_id=d.document_id AND l.case_id=?)");args.append(case_id)
    if query:
        tokens=re.findall(r"[\w]+",query,flags=re.UNICODE)
        fts_query=" AND ".join('"'+x.replace('"','""')+'"' for x in tokens[:12])
        if fts_query:
            try:
                sql="""SELECT d.document_id,d.document_title,d.document_type,d.original_filename,d.imported_at,
                  d.page_count,d.extraction_status,d.file_hash,d.stored_path,
                  snippet(document_text_fts,3,'[',']',' … ',18) AS excerpt,
                  COALESCE(m.record_reference,'') AS record_reference,
                  COALESCE(m.village,'') AS village,COALESCE(m.khasra_numbers,'') AS khasra_numbers
                  FROM document_text_fts JOIN documents d ON d.document_id=document_text_fts.rowid
                  LEFT JOIN revenue_document_metadata m USING(document_id)
                  WHERE document_text_fts MATCH ?"""
                args2=[fts_query]
                if document_type and document_type!="All":sql+=" AND d.document_type=?";args2.append(document_type)
                if case_id is not None:sql+=" AND EXISTS(SELECT 1 FROM revenue_case_document_links l WHERE l.document_id=d.document_id AND l.case_id=?)";args2.append(case_id)
                sql+=" ORDER BY rank LIMIT ?";args2.append(limit)
                matched=conn.execute(sql,args2).fetchall()
                if matched:return matched
            except Exception:
                pass
        like="%"+query+"%"
        where.append("(d.document_title LIKE ? OR d.original_filename LIKE ? OR d.extracted_text LIKE ? OR m.record_reference LIKE ? OR m.khasra_numbers LIKE ? OR m.village LIKE ?)")
        args += [like]*6
    sql="""SELECT d.document_id,d.document_title,d.document_type,d.original_filename,d.imported_at,
      d.page_count,d.extraction_status,d.file_hash,d.stored_path,'' AS excerpt,
      COALESCE(m.record_reference,'') AS record_reference,COALESCE(m.village,'') AS village,
      COALESCE(m.khasra_numbers,'') AS khasra_numbers
      FROM documents d LEFT JOIN revenue_document_metadata m USING(document_id)"""
    if where:sql+=" WHERE "+" AND ".join(where)
    sql+=" ORDER BY d.imported_at DESC,d.document_id DESC LIMIT ?";args.append(limit)
    return conn.execute(sql,args).fetchall()

def document_detail(conn,document_id):
    return conn.execute("""SELECT d.*,m.record_date,m.issuing_authority,m.record_reference,m.village,m.tehsil,
      m.district,m.khasra_numbers,m.khata_number,m.jamabandi_year,m.metadata_status,m.page_notes,m.updated_at AS metadata_updated_at
      FROM documents d LEFT JOIN revenue_document_metadata m USING(document_id) WHERE d.document_id=?""",(document_id,)).fetchone()

def save_document_metadata(conn,document_id,v):
    if not conn.execute("SELECT 1 FROM documents WHERE document_id=?",(document_id,)).fetchone():raise ValueError("Document not found.")
    conn.execute("""INSERT INTO revenue_document_metadata(document_id,record_date,issuing_authority,record_reference,
      village,tehsil,district,khasra_numbers,khata_number,jamabandi_year,metadata_status,page_notes)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(document_id) DO UPDATE SET record_date=excluded.record_date,issuing_authority=excluded.issuing_authority,
      record_reference=excluded.record_reference,village=excluded.village,tehsil=excluded.tehsil,district=excluded.district,
      khasra_numbers=excluded.khasra_numbers,khata_number=excluded.khata_number,jamabandi_year=excluded.jamabandi_year,
      metadata_status=excluded.metadata_status,page_notes=excluded.page_notes,updated_at=CURRENT_TIMESTAMP""",
      (document_id,v.get("record_date") or None,v.get("issuing_authority",""),v.get("record_reference",""),
       v.get("village",""),v.get("tehsil",""),v.get("district",""),v.get("khasra_numbers",""),
       v.get("khata_number",""),v.get("jamabandi_year",""),v.get("metadata_status","unverified"),v.get("page_notes","")))
    conn.commit()

def case_link_options(conn,case_id):
    docs=conn.execute("SELECT document_id,document_title,document_type,original_filename FROM documents ORDER BY document_title").fetchall()
    parties=conn.execute("SELECT party_id,party_name,role FROM revenue_case_parties WHERE case_id=? ORDER BY party_name",(case_id,)).fetchall()
    issues=conn.execute("SELECT issue_id,issue_title FROM revenue_case_issues WHERE case_id=? ORDER BY issue_title",(case_id,)).fetchall()
    return docs,parties,issues

def add_case_document_link(conn,case_id,document_id,values):
    if not conn.execute("SELECT 1 FROM revenue_cases WHERE case_id=?",(case_id,)).fetchone():raise ValueError("Case not found.")
    if not conn.execute("SELECT 1 FROM documents WHERE document_id=?",(document_id,)).fetchone():raise ValueError("Document not found.")
    party_id=values.get("party_id") or None;issue_id=values.get("issue_id") or None
    if party_id and not conn.execute("SELECT 1 FROM revenue_case_parties WHERE party_id=? AND case_id=?",(party_id,case_id)).fetchone():raise ValueError("Selected party does not belong to this case.")
    if issue_id and not conn.execute("SELECT 1 FROM revenue_case_issues WHERE issue_id=? AND case_id=?",(issue_id,case_id)).fetchone():raise ValueError("Selected issue does not belong to this case.")
    kind=values.get("link_type","Evidence");page=values.get("page_reference","")
    existing=conn.execute("""SELECT link_id FROM revenue_case_document_links WHERE case_id=? AND document_id=?
      AND party_id IS ? AND issue_id IS ? AND link_type=? AND page_reference=?""",
      (case_id,document_id,party_id,issue_id,kind,page)).fetchone()
    if existing:return existing["link_id"]
    cur=conn.execute("""INSERT INTO revenue_case_document_links(case_id,document_id,party_id,issue_id,link_type,page_reference,relevance_note,verification_status,notes)
      VALUES(?,?,?,?,?,?,?,?,?)""",(case_id,document_id,party_id,issue_id,kind,page,values.get("relevance_note",""),values.get("verification_status","unverified"),values.get("notes","")))
    conn.commit();return cur.lastrowid

def list_case_document_links(conn,case_id):
    return conn.execute("""SELECT l.*,d.document_title,d.document_type,d.original_filename,d.page_count,
      p.party_name,i.issue_title,m.record_reference,m.village,m.khasra_numbers
      FROM revenue_case_document_links l JOIN documents d USING(document_id)
      LEFT JOIN revenue_case_parties p USING(party_id) LEFT JOIN revenue_case_issues i USING(issue_id)
      LEFT JOIN revenue_document_metadata m USING(document_id)
      WHERE l.case_id=? ORDER BY d.document_title,l.link_id""",(case_id,)).fetchall()

def delete_case_document_link(conn,link_id):
    conn.execute("DELETE FROM revenue_case_document_links WHERE link_id=?",(link_id,));conn.commit()

def build_case_evidence_index(conn,case_id):
    case=conn.execute("SELECT * FROM revenue_cases WHERE case_id=?",(case_id,)).fetchone()
    if not case:raise ValueError("Case not found.")
    rows=list_case_document_links(conn,case_id)
    out=["JASS LEGAL & REVENUE DESK — CASE DOCUMENT / EVIDENCE INDEX","="*72,"",
      f"Case: {case['case_title']}",f"Case number: {case['case_number'] or 'Not recorded'}",
      f"Authority: {case['authority'] or 'Not recorded'}",f"Village / Tehsil / District: {case['village'] or ''} / {case['tehsil'] or ''} / {case['district'] or ''}",
      f"Linked document entries: {len(rows)}",""]
    for n,r in enumerate(rows,1):
        out += [f"{n}. {r['document_title']} (Document ID {r['document_id']})",
          f"   Type: {r['document_type']} | File: {r['original_filename']} | Pages: {r['page_count'] or 'Unknown'}",
          f"   Link classification: {r['link_type']} | Party: {r['party_name'] or '—'} | Issue: {r['issue_title'] or '—'}",
          f"   Page / paragraph reference: {r['page_reference'] or 'Not recorded'}",
          f"   Record reference: {r['record_reference'] or 'Not recorded'} | Village: {r['village'] or 'Not recorded'} | Khasra: {r['khasra_numbers'] or 'Not recorded'}",
          f"   Relevance: {r['relevance_note']}",f"   Verification: {r['verification_status']}",f"   Notes: {r['notes']}",""]
    out += ["IMPORTANT: This index lists documents linked by the user. It does not establish authenticity, admissibility, ownership, title, completeness or legal effect. Check originals, certified copies, page numbering, context and applicable evidentiary/procedural requirements."]
    return "\n".join(out)
