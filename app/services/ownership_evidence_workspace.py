"""Cross-year ownership history and evidence traceability for Haryana revenue records.

Outputs describe registered local data and arithmetic comparisons only; they do not
determine title, validity of mutation, succession or legal entitlement.
"""
import re

def _norm(value):
    return " ".join((value or "").casefold().split())

def list_villages(conn,case_id=None):
    sql="SELECT DISTINCT village,district,tehsil,hadbast_number FROM revenue_record_sets WHERE 1=1"
    args=[]
    if case_id is not None:sql+=" AND case_id=?";args.append(case_id)
    sql+=" ORDER BY village"
    return conn.execute(sql,args).fetchall()

def ownership_history(conn,village,case_id=None,khasra=None):
    sql="""SELECT s.record_set_id,s.record_type,s.record_year,s.village,s.tehsil,s.district,s.hadbast_number,
      s.source_reference,s.source_document_id,s.verification_status AS set_verification,s.notes AS set_notes,
      e.entry_id,e.khewat_number,e.khata_number,e.khatauni_number,e.khasra_number,e.owner_name,e.parent_name,
      e.area_value,e.area_unit,e.share_numerator,e.share_denominator,e.entry_notes
      FROM revenue_record_sets s JOIN revenue_record_entries e USING(record_set_id)
      WHERE lower(s.village)=lower(?)"""
    args=[village]
    if case_id is not None:sql+=" AND s.case_id=?";args.append(case_id)
    if khasra:sql+=" AND lower(e.khasra_number)=lower(?)";args.append(khasra.strip())
    sql+=" ORDER BY s.record_year,s.record_set_id,e.khasra_number,e.owner_name,e.entry_id"
    return conn.execute(sql,args).fetchall()

def mutation_history(conn,village=None,case_id=None,khasra=None):
    sql="""SELECT m.*,s.village AS set_village,s.record_year AS linked_record_year,
      s.source_document_id AS set_document_id,c.case_title
      FROM revenue_mutation_records m LEFT JOIN revenue_record_sets s USING(record_set_id)
      LEFT JOIN revenue_cases c USING(case_id) WHERE 1=1"""
    args=[]
    if village:sql+=" AND lower(COALESCE(s.village,c.village,''))=lower(?)";args.append(village)
    if case_id is not None:sql+=" AND m.case_id=?";args.append(case_id)
    if khasra:
        # Search token boundaries in comma/semicolon/space-separated Khasra references.
        sql+=" AND (','||replace(replace(replace(lower(COALESCE(m.khasra_numbers,'')),' ',''),';',','),'،',',')||',') LIKE ?"
        args.append("%,"+khasra.strip().lower().replace(" ","")+",%")
    sql+=" ORDER BY COALESCE(m.mutation_date,'') ,m.mutation_id"
    return conn.execute(sql,args).fetchall()

def compare_ownership_years(conn,village,earlier_set_id,later_set_id):
    sets=conn.execute("SELECT * FROM revenue_record_sets WHERE record_set_id IN (?,?)",(earlier_set_id,later_set_id)).fetchall()
    if len(sets)!=2:raise ValueError("Both record sets must exist.")
    byid={r["record_set_id"]:r for r in sets};a=byid[earlier_set_id];b=byid[later_set_id]
    if _norm(a["village"])!=_norm(village) or _norm(b["village"])!=_norm(village):
        raise ValueError("Both record sets must belong to the selected village.")
    def load(rid):
        rows=conn.execute("SELECT * FROM revenue_record_entries WHERE record_set_id=? ORDER BY khasra_number,owner_name,entry_id",(rid,)).fetchall()
        result={}
        for r in rows:result.setdefault((_norm(r["khasra_number"]),_norm(r["owner_name"])),[]).append(r)
        return result
    left,right=load(earlier_set_id),load(later_set_id);results=[]
    for key in sorted(set(left)|set(right)):
        old,new=left.get(key,[]),right.get(key,[])
        if not old:status="Added in later snapshot";changes=[]
        elif not new:status="Absent from later snapshot";changes=[]
        else:
            x,y=old[0],new[0];changes=[]
            for field,label in [("khewat_number","Khewat"),("khata_number","Khata"),("khatauni_number","Khatauni"),("area_value","Area value"),("area_unit","Area unit"),("share_numerator","Share numerator"),("share_denominator","Share denominator"),("parent_name","Parent name")]:
                if x[field]!=y[field]:changes.append(label)
            if len(old)>1 or len(new)>1:changes.append("Multiple matching rows — manual review")
            status="Changed: "+", ".join(changes) if changes else "No difference detected"
        results.append({"khasra":(new or old)[0]["khasra_number"],"owner":(new or old)[0]["owner_name"],
          "earlier_rows":len(old),"later_rows":len(new),"status":status})
    return a,b,results

def evidence_trace(conn,village,case_id=None):
    sql="""SELECT s.record_set_id,s.record_type,s.record_year,s.village,s.source_reference,
      s.verification_status AS record_verification,s.source_document_id,d.document_title,d.original_filename,
      l.link_id,l.case_id,l.link_type,l.page_reference,l.relevance_note,l.verification_status AS link_verification,
      c.case_title
      FROM revenue_record_sets s LEFT JOIN documents d ON d.document_id=s.source_document_id
      LEFT JOIN revenue_case_document_links l ON l.document_id=s.source_document_id
      LEFT JOIN revenue_cases c ON c.case_id=l.case_id
      WHERE lower(s.village)=lower(?)"""
    args=[village]
    if case_id is not None:
        sql+=" AND (s.case_id=? OR l.case_id=?)";args.extend([case_id,case_id])
    sql+=" ORDER BY s.record_year,s.record_set_id,l.link_id"
    return conn.execute(sql,args).fetchall()

def list_review_items(conn,case_id):
    return conn.execute("""SELECT r.*,d.document_title FROM revenue_ownership_review_items r
      LEFT JOIN documents d ON d.document_id=r.source_document_id WHERE r.case_id=?
      ORDER BY CASE r.review_status WHEN 'Open' THEN 0 WHEN 'Under review' THEN 1 ELSE 2 END,r.khasra_number,r.review_item_id""",(case_id,)).fetchall()

def add_review_item(conn,case_id,v):
    if not (v.get("observation") or "").strip():raise ValueError("Describe the record observation or discrepancy.")
    cur=conn.execute("""INSERT INTO revenue_ownership_review_items(case_id,village,khasra_number,owner_name,review_type,
      observation,question_for_review,source_document_id,page_reference,review_status,verification_status,resolution_note)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(case_id,v.get("village",""),v.get("khasra_number",""),v.get("owner_name",""),
      v.get("review_type","Discrepancy"),v["observation"].strip(),v.get("question_for_review",""),v.get("source_document_id") or None,
      v.get("page_reference",""),v.get("review_status","Open"),v.get("verification_status","unverified"),v.get("resolution_note","")))
    conn.commit();return cur.lastrowid

def update_review_item(conn,item_id,v):
    conn.execute("""UPDATE revenue_ownership_review_items SET review_type=?,observation=?,question_for_review=?,
      page_reference=?,review_status=?,verification_status=?,resolution_note=?,updated_at=CURRENT_TIMESTAMP
      WHERE review_item_id=?""",(v.get("review_type","Discrepancy"),v.get("observation",""),v.get("question_for_review",""),
      v.get("page_reference",""),v.get("review_status","Open"),v.get("verification_status","unverified"),v.get("resolution_note",""),item_id))
    conn.commit()

def delete_review_item(conn,item_id):
    conn.execute("DELETE FROM revenue_ownership_review_items WHERE review_item_id=?",(item_id,));conn.commit()

def build_ownership_history_report(conn,village,case_id=None,khasra=None):
    rows=ownership_history(conn,village,case_id,khasra);muts=mutation_history(conn,village,case_id,khasra)
    traces=evidence_trace(conn,village,case_id)
    out=["JASS LEGAL & REVENUE DESK — OWNERSHIP HISTORY & EVIDENCE REPORT","="*76,"",
      f"Village: {village}",f"Case ID: {case_id or 'All linked / registered records'}",f"Khasra filter: {khasra or 'All'}",
      f"Ownership entry rows: {len(rows)}",f"Mutation entries: {len(muts)}","","OWNERSHIP SNAPSHOTS BY YEAR"]
    grouped={}
    for r in rows:grouped.setdefault((r["record_year"],r["record_set_id"],r["khasra_number"]),[]).append(r)
    for (year,rid,khasra_no),items in grouped.items():
        out.append(f"\n{year} — Record set #{rid} — Khasra {khasra_no} — source status: {items[0]['set_verification']}")
        for r in items:
            share=f"{r['share_numerator']}/{r['share_denominator']}" if r["share_denominator"] else "Not recorded"
            out.append(f"  • {r['owner_name']} (parent: {r['parent_name'] or '—'}); Khewat {r['khewat_number'] or '—'}; Khata {r['khata_number'] or '—'}; Khatauni {r['khatauni_number'] or '—'}; area {r['area_value']} {r['area_unit']}; share {share}")
    out += ["","MUTATION HISTORY"]
    for r in muts:out.append(f"- Mutation {r['mutation_number']} | {r['mutation_date'] or 'date not recorded'} | {r['mutation_type']} | {r['from_party'] or '—'} → {r['to_party'] or '—'} | Khasra {r['khasra_numbers'] or '—'} | status {r['status']} | source {r['source_reference'] or '—'}")
    out += ["","SOURCE DOCUMENT TRACE"]
    seen=set()
    for r in traces:
        key=(r["record_set_id"],r["source_document_id"],r["link_id"])
        if key in seen:continue
        seen.add(key)
        out.append(f"- Record set #{r['record_set_id']} ({r['record_year']}): {r['document_title'] or 'No linked source document'}; source reference {r['source_reference'] or '—'}; record verification {r['record_verification']}; case link {r['case_title'] or '—'}; page {r['page_reference'] or '—'}; link verification {r['link_verification'] or '—'}")
    out += ["","LIMITATIONS","- This report is a transcription and comparison of records registered in this local database, not a certified revenue extract or title opinion.",
      "- A change between snapshots does not prove the legal cause or validity of the change. Trace mutations and inspect underlying orders and original records.",
      "- Owner-name matching is literal after case/whitespace normalization; spelling, aliases, inheritance, joint holdings, partition, possession and legal status require human review.",
      "- Missing local entries do not establish absence of rights or records. Confirm complete record periods and original/certified sources."]
    return "\n".join(out)
