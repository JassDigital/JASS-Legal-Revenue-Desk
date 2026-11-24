"""Transparent co-sharer and proposed partition arithmetic; not a title adjudicator."""
from app.services.revenue_records_service import AREA_TO_ACRE, area_in_acres

PLAN_STATUSES=["Working","For review","Proposed","Superseded","Final reference"]
def list_plans(conn):
    return conn.execute("""SELECT p.*,s.village,s.record_year,c.case_title FROM revenue_partition_plans p
        JOIN revenue_record_sets s USING(record_set_id) LEFT JOIN revenue_cases c USING(case_id)
        ORDER BY p.updated_at DESC,p.plan_id DESC""").fetchall()
def create_plan(conn,values):
    if not values.get("plan_title","").strip():raise ValueError("Plan title is required.")
    if not values.get("record_set_id"):raise ValueError("Select a source record set.")
    cur=conn.execute("""INSERT INTO revenue_partition_plans(case_id,record_set_id,plan_title,plan_status,basis_notes,assumptions)
        VALUES(?,?,?,?,?,?)""",(values.get("case_id") or None,values["record_set_id"],values["plan_title"].strip(),
        values.get("plan_status","Working"),values.get("basis_notes",""),values.get("assumptions","")))
    conn.commit();return cur.lastrowid
def get_plan(conn,plan_id):
    return conn.execute("SELECT * FROM revenue_partition_plans WHERE plan_id=?",(plan_id,)).fetchone()
def update_plan(conn,plan_id,values):
    conn.execute("""UPDATE revenue_partition_plans SET plan_title=?,plan_status=?,basis_notes=?,assumptions=?,
        updated_at=CURRENT_TIMESTAMP WHERE plan_id=?""",(values["plan_title"].strip(),values["plan_status"],
        values.get("basis_notes",""),values.get("assumptions",""),plan_id));conn.commit()
def delete_plan(conn,plan_id):
    conn.execute("DELETE FROM revenue_partition_plans WHERE plan_id=?",(plan_id,));conn.commit()
def analyse_ownership(conn,record_set_id):
    rs=conn.execute("SELECT * FROM revenue_record_sets WHERE record_set_id=?",(record_set_id,)).fetchone()
    if not rs:raise ValueError("Record set not found.")
    source=conn.execute("SELECT * FROM revenue_record_entries WHERE record_set_id=? ORDER BY khasra_number,owner_name,entry_id",(record_set_id,)).fetchall()
    parcels={}
    for r in source:parcels.setdefault(r["khasra_number"],[]).append(r)
    khasra_results=[];owner_totals={};flags=[]
    for khasra,rows in sorted(parcels.items()):
        shares=[];areas=[];names=set();seen=set()
        for r in rows:
            name=r["owner_name"].strip()
            if name.casefold() in seen:
                flags.append(f"Khasra {khasra}: repeated entry for {name}; check whether entries are duplicates or separate interests.")
            seen.add(name.casefold());names.add(name)
            if r["share_numerator"] is not None and r["share_denominator"]:
                frac=r["share_numerator"]/r["share_denominator"];shares.append(frac)
                if name not in owner_totals:owner_totals[name]={"share_entries":0,"entitlement_acres":0.0,"unknown_area_entries":0}
                owner_totals[name]["share_entries"]+=1
            else:frac=None
            if r["area_value"] is not None:
                try:areas.append(area_in_acres(r["area_value"],r["area_unit"]))
                except ValueError:flags.append(f"Khasra {khasra}: unknown area unit {r['area_unit']}.")
            if frac is not None and r["area_value"] is not None:
                owner_totals.setdefault(name,{"share_entries":0,"entitlement_acres":0.0,"unknown_area_entries":0})
                owner_totals[name]["entitlement_acres"]+=area_in_acres(r["area_value"],r["area_unit"])*frac
            elif frac is not None:
                owner_totals.setdefault(name,{"share_entries":0,"entitlement_acres":0.0,"unknown_area_entries":0})
                owner_totals[name]["unknown_area_entries"]+=1
        unique_areas=sorted(set(round(x,8) for x in areas))
        parcel_area=unique_areas[0] if len(unique_areas)==1 else None
        total=sum(shares) if len(shares)==len(rows) else None
        if total is None:status="Incomplete share data"
        elif abs(total-1)<1e-6:status="Shares total 100%"
        elif total<1:status=f"Shares total {total*100:.2f}% — shortfall"
        else:status=f"Shares total {total*100:.2f}% — exceeds 100%"
        if len(unique_areas)>1:
            flags.append(f"Khasra {khasra}: multiple parcel-area values were entered; parcel total cannot be inferred safely.")
        if total is not None and total>1.000001:flags.append(f"Khasra {khasra}: recorded share fractions total more than 1.")
        if total is not None and total<0.999999:flags.append(f"Khasra {khasra}: recorded share fractions total less than 1.")
        if len(rows)>1 and parcel_area is None and areas:
            flags.append(f"Khasra {khasra}: area basis is ambiguous; check if the entered area repeats the full parcel area for each co-sharer.")
        khasra_results.append({"khasra":khasra,"owners":", ".join(sorted(names)),"owner_count":len(rows),
            "parcel_area_acres":parcel_area,"share_total":total,"share_status":status})
    return rs,khasra_results,owner_totals,flags
def list_allocations(conn,plan_id):
    return conn.execute("SELECT * FROM revenue_partition_allocations WHERE plan_id=? ORDER BY khasra_number,co_sharer_name,allocation_id",(plan_id,)).fetchall()
def add_allocation(conn,plan_id,values):
    if not values.get("khasra_number","").strip() or not values.get("co_sharer_name","").strip():
        raise ValueError("Khasra number and co-sharer name are required.")
    area=float(values.get("proposed_area",0))
    if area<0:raise ValueError("Proposed area cannot be negative.")
    unit=values.get("area_unit","acre")
    if unit not in AREA_TO_ACRE:raise ValueError("Unknown area unit.")
    num=values.get("proposed_share_numerator");den=values.get("proposed_share_denominator")
    if (num is None)!=(den is None):raise ValueError("Enter both proposed share numerator and denominator, or leave both blank.")
    if den is not None and (int(den)<=0 or int(num)<0 or int(num)>int(den)):raise ValueError("Invalid proposed share.")
    conn.execute("""INSERT INTO revenue_partition_allocations(plan_id,khasra_number,co_sharer_name,proposed_area,
        area_unit,proposed_share_numerator,proposed_share_denominator,location_or_quality_notes)
        VALUES(?,?,?,?,?,?,?,?)""",(plan_id,values["khasra_number"].strip(),values["co_sharer_name"].strip(),area,unit,num,den,values.get("location_or_quality_notes","")))
    conn.commit()
def delete_allocation(conn,allocation_id):
    conn.execute("DELETE FROM revenue_partition_allocations WHERE allocation_id=?",(allocation_id,));conn.commit()
def analyse_plan(conn,plan_id):
    plan=get_plan(conn,plan_id)
    if not plan:raise ValueError("Plan not found.")
    _,base,_,base_flags=analyse_ownership(conn,plan["record_set_id"])
    base_by={r["khasra"]:r for r in base};allocs=list_allocations(conn,plan_id);groups={}
    for r in allocs:groups.setdefault(r["khasra_number"],[]).append(r)
    rows=[];flags=list(base_flags)
    for khasra,items in sorted(groups.items()):
        area=sum(area_in_acres(r["proposed_area"],r["area_unit"]) for r in items)
        shares=[r["proposed_share_numerator"]/r["proposed_share_denominator"] for r in items if r["proposed_share_denominator"]]
        share_complete=all(r["proposed_share_denominator"] for r in items)
        share_total=sum(shares) if share_complete else None
        source_area=base_by.get(khasra,{}).get("parcel_area_acres")
        result="No source parcel area available"
        if source_area is not None:
            diff=area-source_area
            if abs(diff)<0.0001:result="Proposed area matches entered source area"
            elif diff>0:result=f"Proposed area exceeds source by {diff:.6f} acres"
            else:result=f"Proposed area short by {abs(diff):.6f} acres"
            if abs(diff)>0.0001:flags.append(f"Khasra {khasra}: {result}.")
        if share_total is not None and abs(share_total-1)>0.000001:
            flags.append(f"Khasra {khasra}: proposed share fractions total {share_total*100:.2f}%, not 100%.")
        if len({r["co_sharer_name"].casefold() for r in items})<len(items):
            flags.append(f"Khasra {khasra}: multiple allocation rows for the same co-sharer; review.")
        rows.append({"khasra":khasra,"allocations":len(items),"proposed_area_acres":area,
            "source_area_acres":source_area,"proposed_share_total":share_total,"comparison":result})
    return plan,rows,flags
def build_partition_report(conn,plan_id):
    plan,rows,flags=analyse_plan(conn,plan_id)
    record=conn.execute("SELECT * FROM revenue_record_sets WHERE record_set_id=?",(plan["record_set_id"],)).fetchone()
    out=["JASS LEGAL & REVENUE DESK — PARTITION WORKING STATEMENT","="*68,"",
        f"Plan: {plan['plan_title']}",f"Status: {plan['plan_status']}",f"Village: {record['village']}",
        f"Record year/period: {record['record_year']}",f"Record verification: {record['verification_status']}",
        f"Case ID: {plan['case_id'] or 'Not linked'}","","BASIS / NOTES",plan["basis_notes"],
        "ASSUMPTIONS",plan["assumptions"],"","RECORDED OWNERSHIP ANALYSIS"]
    _,base,owners,base_flags=analyse_ownership(conn,plan["record_set_id"])
    for r in base:out.append(f"- Khasra {r['khasra']}: {r['owners']}; rows {r['owner_count']}; parcel area acres {r['parcel_area_acres']}; share result: {r['share_status']}")
    out += ["","PROPOSED ALLOCATIONS"]
    for r in list_allocations(conn,plan_id):
        share=f"{r['proposed_share_numerator']}/{r['proposed_share_denominator']}" if r["proposed_share_denominator"] else "Not entered"
        out.append(f"- Khasra {r['khasra_number']}: {r['co_sharer_name']} — {r['proposed_area']} {r['area_unit']}; proposed share {share}; {r['location_or_quality_notes']}")
    out += ["","PROPOSED AREA RECONCILIATION"]
    for r in rows:out.append(f"- Khasra {r['khasra']}: proposed {r['proposed_area_acres']:.6f} acres; source {r['source_area_acres']}; {r['comparison']}")
    out += ["","REVIEW FLAGS"]
    out.extend("- "+f for f in flags) if flags else out.append("- No arithmetic flags were generated from the entered data.")
    out += ["","DISCLAIMER: This is an arithmetic working statement based solely on user-entered data. It is not a partition order, survey, title opinion, valuation, or determination of legal entitlement. Verify certified records, actual possession, dimensions, access, irrigation, soil/quality, encumbrances, applicable law and authority directions before relying on any proposal."]
    return "\n".join(out)
