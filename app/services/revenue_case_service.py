"""Offline case-management operations for personal Haryana revenue matters."""
CASE_TYPES = ["Mutation", "Jamabandi / Record of Rights", "Partition", "Inheritance", "Girdawari", "Appeal", "Revision", "Correction", "Abadi Deh", "Other"]
CASE_STATUSES = ["Preparing", "Filed", "Pending", "Awaiting Order", "Decided", "Appeal / Revision", "Closed"]
PARTY_ROLES = ["Applicant", "Petitioner", "Appellant", "Respondent", "Opposite party", "Co-sharer", "Witness", "Other"]

def list_cases(conn, query="", status="All"):
    sql = "SELECT * FROM revenue_cases WHERE 1=1"
    args=[]
    if query.strip():
        like="%"+query.strip()+"%"
        sql += " AND (case_title LIKE ? OR case_number LIKE ? OR village LIKE ? OR tehsil LIKE ? OR district LIKE ? OR authority LIKE ?)"
        args.extend([like]*6)
    if status != "All":
        sql += " AND status=?"; args.append(status)
    sql += " ORDER BY CASE WHEN next_hearing_date IS NULL OR next_hearing_date='' THEN 1 ELSE 0 END, next_hearing_date, updated_at DESC"
    return conn.execute(sql,args).fetchall()

def create_case(conn, values):
    keys=["case_title","case_type","case_number","authority","district","tehsil","village","filing_date","status","next_hearing_date","priority","case_summary","strategy_notes"]
    if not values.get("case_title","").strip(): raise ValueError("Case title is required.")
    cur=conn.execute("INSERT INTO revenue_cases("+",".join(keys)+") VALUES("+",".join("?" for _ in keys)+")",[values.get(k) or None if k in ("case_number","authority","district","tehsil","village","filing_date","next_hearing_date") else values.get(k,"") for k in keys])
    conn.commit(); return cur.lastrowid

def update_case(conn, case_id, values):
    keys=["case_title","case_type","case_number","authority","district","tehsil","village","filing_date","status","next_hearing_date","priority","case_summary","strategy_notes"]
    if not values.get("case_title","").strip(): raise ValueError("Case title is required.")
    conn.execute("UPDATE revenue_cases SET "+",".join(k+"=?" for k in keys)+",updated_at=CURRENT_TIMESTAMP WHERE case_id=?",
        [values.get(k) or None if k in ("case_number","authority","district","tehsil","village","filing_date","next_hearing_date") else values.get(k,"") for k in keys]+[case_id])
    conn.commit()

def case_detail(conn, case_id):
    return conn.execute("SELECT * FROM revenue_cases WHERE case_id=?",(case_id,)).fetchone()

def add_party(conn, case_id, values):
    conn.execute("""INSERT INTO revenue_case_parties(case_id,party_name,role,address,contact_notes,representative)
        VALUES(?,?,?,?,?,?)""",(case_id,values["party_name"],values["role"],values["address"],values["contact_notes"],values["representative"]))
    conn.commit()

def parties(conn, case_id):
    return conn.execute("SELECT * FROM revenue_case_parties WHERE case_id=? ORDER BY party_id",(case_id,)).fetchall()

def add_property(conn, case_id, values):
    conn.execute("""INSERT INTO revenue_case_properties(case_id,village,tehsil,district,hadbast_number,jamabandi_year,
        khata_number,khatauni_number,khasra_numbers,area,ownership_share,land_description)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(case_id,*[values.get(k,"") for k in ["village","tehsil","district","hadbast_number","jamabandi_year","khata_number","khatauni_number","khasra_numbers","area","ownership_share","land_description"]]))
    conn.commit()

def properties(conn, case_id):
    return conn.execute("SELECT * FROM revenue_case_properties WHERE case_id=? ORDER BY property_id",(case_id,)).fetchall()

def add_event(conn, case_id, values):
    conn.execute("""INSERT INTO revenue_case_events(case_id,event_date,event_type,title,details,next_action)
        VALUES(?,?,?,?,?,?)""",(case_id,values["event_date"] or None,values["event_type"],values["title"],values["details"],values["next_action"]))
    conn.commit()

def events(conn, case_id):
    return conn.execute("SELECT * FROM revenue_case_events WHERE case_id=? ORDER BY COALESCE(event_date,'') DESC,event_id DESC",(case_id,)).fetchall()

def add_evidence(conn, case_id, values):
    conn.execute("""INSERT INTO revenue_case_evidence(case_id,document_id,evidence_title,evidence_type,document_reference,relevance_notes,verification_status)
        VALUES(?,?,?,?,?,?,?)""",(case_id,values["document_id"] or None,values["evidence_title"],values["evidence_type"],values["document_reference"],values["relevance_notes"],values["verification_status"]))
    conn.commit()

def evidence(conn, case_id):
    return conn.execute("""SELECT e.*,d.document_title AS linked_document FROM revenue_case_evidence e
        LEFT JOIN documents d ON d.document_id=e.document_id WHERE e.case_id=? ORDER BY e.evidence_id DESC""",(case_id,)).fetchall()

def add_issue(conn, case_id, values):
    conn.execute("""INSERT INTO revenue_case_issues(case_id,issue_title,facts,legal_question,proposed_argument,relevant_law,status)
        VALUES(?,?,?,?,?,?,?)""",(case_id,values["issue_title"],values["facts"],values["legal_question"],values["proposed_argument"],values["relevant_law"],values["status"]))
    conn.commit()

def issues(conn, case_id):
    return conn.execute("SELECT * FROM revenue_case_issues WHERE case_id=? ORDER BY issue_id DESC",(case_id,)).fetchall()

def delete_case(conn, case_id):
    conn.execute("DELETE FROM revenue_cases WHERE case_id=?",(case_id,)); conn.commit()
