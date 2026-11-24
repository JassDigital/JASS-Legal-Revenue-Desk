"""Revenue record register, mutation history, comparisons and arithmetic."""
AREA_TO_ACRE={"acre":1.0,"kanal":1/8,"marla":1/160,"sq_yard":1/4840,"hectare":2.4710538147,"sq_metre":1/4046.8564224}
AREA_UNITS=list(AREA_TO_ACRE)
RECORD_TYPES=["Jamabandi","Mutation","Girdawari","Fard / Record extract","Other"]
VERIFICATION=["unverified","source_checked","copy_compared","disputed"]
def record_sets(conn):
    return conn.execute("""SELECT s.*,c.case_title,d.document_title FROM revenue_record_sets s
        LEFT JOIN revenue_cases c USING(case_id) LEFT JOIN documents d ON d.document_id=s.source_document_id
        ORDER BY s.village,s.record_year DESC,s.record_set_id DESC""").fetchall()
def add_record_set(conn,v):
    if not v.get("village","").strip() or not v.get("record_year","").strip():raise ValueError("Village and record year are required.")
    cur=conn.execute("""INSERT INTO revenue_record_sets(case_id,record_type,record_year,district,tehsil,village,
        hadbast_number,estate_name,source_reference,source_document_id,verification_status,notes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",tuple(v.get(k) or None for k in ["case_id","record_type","record_year","district","tehsil","village","hadbast_number","estate_name","source_reference","source_document_id"])+ (v.get("verification_status","unverified"),v.get("notes","")))
    conn.commit();return cur.lastrowid
def delete_record_set(conn,rid):
    conn.execute("DELETE FROM revenue_record_sets WHERE record_set_id=?",(rid,));conn.commit()
def entries(conn,rid=None):
    sql="""SELECT e.*,s.record_year,s.village,s.record_type FROM revenue_record_entries e
        JOIN revenue_record_sets s USING(record_set_id)"""
    args=()
    if rid is not None:sql+=" WHERE e.record_set_id=?";args=(rid,)
    sql+=" ORDER BY s.village,s.record_year DESC,e.khasra_number,e.owner_name"
    return conn.execute(sql,args).fetchall()
def add_entry(conn,rid,v):
    if not v.get("khasra_number","").strip() or not v.get("owner_name","").strip():raise ValueError("Khasra number and owner name are required.")
    num=v.get("share_numerator");den=v.get("share_denominator")
    if (num is None) != (den is None):raise ValueError("Enter both share numerator and denominator, or leave both blank.")
    if den is not None and (int(den)<=0 or int(num)<0 or int(num)>int(den)):raise ValueError("Share must be between zero and one.")
    area=v.get("area_value")
    if area is not None and float(area)<0:raise ValueError("Area cannot be negative.")
    conn.execute("""INSERT INTO revenue_record_entries(record_set_id,khewat_number,khata_number,khatauni_number,
        khasra_number,owner_name,parent_name,area_value,area_unit,share_numerator,share_denominator,entry_notes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(rid,v.get("khewat_number"),v.get("khata_number"),v.get("khatauni_number"),
        v["khasra_number"],v["owner_name"],v.get("parent_name"),area,v.get("area_unit","acre"),num,den,v.get("entry_notes","")))
    conn.commit()
def mutations(conn):
    return conn.execute("""SELECT m.*,s.village FROM revenue_mutation_records m
        LEFT JOIN revenue_record_sets s USING(record_set_id)
        ORDER BY COALESCE(m.mutation_date,'') DESC,m.mutation_id DESC""").fetchall()
def add_mutation(conn,v):
    if not v.get("mutation_number","").strip():raise ValueError("Mutation number is required.")
    num=v.get("share_numerator");den=v.get("share_denominator")
    if (num is None)!=(den is None):raise ValueError("Enter both share numerator and denominator, or leave both blank.")
    if den is not None and (int(den)<=0 or int(num)<0 or int(num)>int(den)):raise ValueError("Invalid share fraction.")
    conn.execute("""INSERT INTO revenue_mutation_records(record_set_id,case_id,mutation_number,mutation_date,mutation_type,
        khasra_numbers,from_party,to_party,area_value,area_unit,share_numerator,share_denominator,status,source_reference,notes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(v.get("record_set_id") or None,v.get("case_id") or None,v["mutation_number"],
        v.get("mutation_date") or None,v.get("mutation_type","Other"),v.get("khasra_numbers"),v.get("from_party"),v.get("to_party"),
        v.get("area_value") or None,v.get("area_unit","acre"),num,den,v.get("status","Unverified"),v.get("source_reference"),v.get("notes","")))
    conn.commit()
def area_in_acres(value,unit):
    if unit not in AREA_TO_ACRE:raise ValueError("Unknown area unit.")
    return float(value)*AREA_TO_ACRE[unit]
def share_area(value,unit,numerator,denominator):
    if denominator is None or int(denominator)<=0:raise ValueError("A valid share fraction is required.")
    return area_in_acres(value,unit)*int(numerator)/int(denominator)
def compare_record_sets(conn,left_id,right_id):
    left=conn.execute("SELECT * FROM revenue_record_sets WHERE record_set_id=?",(left_id,)).fetchone()
    right=conn.execute("SELECT * FROM revenue_record_sets WHERE record_set_id=?",(right_id,)).fetchone()
    if not left or not right:raise ValueError("Both record sets must exist.")
    if left["village"].casefold()!=right["village"].casefold():raise ValueError("Compare records from the same village.")
    def keyrow(r):return (r["khasra_number"].strip().casefold(),r["owner_name"].strip().casefold())
    def load(rid):
        data={}
        for r in entries(conn,rid):
            k=keyrow(r);data.setdefault(k,[]).append(r)
        return data
    a,b=load(left_id),load(right_id);results=[]
    for k in sorted(set(a)|set(b)):
        ar=a.get(k,[]);br=b.get(k,[])
        if not ar:status="Added in later record"
        elif not br:status="Missing in later record"
        else:
            old,new=ar[0],br[0];changes=[]
            for field,label in [("khewat_number","Khewat"),("khata_number","Khata"),("khatauni_number","Khatauni"),("area_value","Area"),("area_unit","Area unit"),("share_numerator","Share numerator"),("share_denominator","Share denominator")]:
                if old[field]!=new[field]:changes.append(label)
            status="Changed: "+", ".join(changes) if changes else "No difference detected"
        results.append({"khasra":k[0],"owner":k[1],"status":status,"earlier_count":len(ar),"later_count":len(br)})
    return left,right,results
def record_integrity_flags(conn,rid):
    rows=entries(conn,rid);flags=[]
    groups={}
    for r in rows:groups.setdefault(r["khasra_number"],[]).append(r)
    for khasra,items in groups.items():
        total=0;complete=True
        for r in items:
            if r["share_numerator"] is None or r["share_denominator"] is None:complete=False
            else:total+=r["share_numerator"]/r["share_denominator"]
        if complete and total>1.0000001:flags.append(f"Khasra {khasra}: entered owner shares total {total:.4f}, exceeding 1. Check duplicate/overlapping entries and source.")
        areas=[(r["area_value"],r["area_unit"]) for r in items if r["area_value"] is not None]
        if len(areas)>1:
            converted=[area_in_acres(v,u) for v,u in areas]
            if max(converted)-min(converted)>0.0001:flags.append(f"Khasra {khasra}: area values differ between owner entries. Confirm whether area is parcel total or owner-wise.")
    return flags
