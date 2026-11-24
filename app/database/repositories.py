class LegislationRepository:
    def __init__(self, conn): self.conn = conn
    def list(self, query="", jurisdiction="All", limit=500):
        sql = "SELECT * FROM legislation WHERE 1=1"; args = []
        if query:
            p=f"%{query}%"; sql += " AND (title LIKE ? OR short_title LIKE ? OR act_number LIKE ?)"; args += [p,p,p]
        if jurisdiction != "All": sql += " AND jurisdiction=?"; args.append(jurisdiction)
        sql += " ORDER BY year DESC,title LIMIT ?"; args.append(limit)
        return self.conn.execute(sql,args).fetchall()
    def create(self, title, short_title="", act_number="", year=None, jurisdiction="Haryana"):
        cur=self.conn.execute("""INSERT INTO legislation(title,short_title,act_number,year,jurisdiction,current_status)
            VALUES(?,?,?,?,?,'unverified')""",(title,short_title,act_number,year,jurisdiction))
        self.conn.commit(); return cur.lastrowid

class JudgmentRepository:
    def __init__(self, conn): self.conn=conn
    def create(self, case_title, case_number="", citation="", decision_date="", judge_names="",
               official_url="", full_text="", verification_status="unverified",
               court_name="", petitioner="", respondent="", subject_keywords="", paragraph_reference=""):
        cur=self.conn.execute("""INSERT INTO judgments(
            case_title,case_number,citation,decision_date,judge_names,official_url,full_text,
            verification_status,court_name,petitioner,respondent,subject_keywords,paragraph_reference)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (case_title,case_number,citation,decision_date,judge_names,official_url,full_text,
             verification_status,court_name,petitioner,respondent,subject_keywords,paragraph_reference))
        self.conn.commit(); return cur.lastrowid
    def get(self, judgment_id):
        return self.conn.execute("SELECT * FROM judgments WHERE judgment_id=?",(judgment_id,)).fetchone()
    def list(self, query="", court="All", year="", verification="All", topic="All", limit=500):
        sql="""SELECT j.* FROM judgments j WHERE 1=1"""; args=[]
        if query:
            p=f"%{query}%"
            sql += """ AND (j.case_title LIKE ? OR j.case_number LIKE ? OR j.citation LIKE ?
                       OR j.petitioner LIKE ? OR j.respondent LIKE ? OR j.judge_names LIKE ?
                       OR j.subject_keywords LIKE ? OR j.full_text LIKE ?)"""
            args += [p]*8
        if court != "All": sql += " AND j.court_name=?"; args.append(court)
        if year: sql += " AND substr(j.decision_date,1,4)=?"; args.append(str(year))
        if verification != "All": sql += " AND j.verification_status=?"; args.append(verification)
        if topic != "All":
            sql += """ AND EXISTS(SELECT 1 FROM judgment_topics t
                                  WHERE t.judgment_id=j.judgment_id AND t.normalized_topic=?)"""
            args.append(topic.casefold())
        sql += " ORDER BY j.decision_date DESC,j.judgment_id DESC LIMIT ?"; args.append(limit)
        return self.conn.execute(sql,args).fetchall()
    def courts(self):
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT court_name FROM judgments WHERE court_name IS NOT NULL AND court_name<>'' ORDER BY court_name")]
    def topics(self):
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT topic FROM judgment_topics ORDER BY topic")]

class DocumentRepository:
    def __init__(self, conn): self.conn=conn
    def list(self, query="", document_type="All", limit=500):
        sql="SELECT * FROM documents WHERE 1=1"; args=[]
        if query:
            p=f"%{query}%"; sql+=" AND (document_title LIKE ? OR original_filename LIKE ?)"; args += [p,p]
        if document_type!="All": sql+=" AND document_type=?"; args.append(document_type)
        sql+=" ORDER BY imported_at DESC LIMIT ?"; args.append(limit)
        return self.conn.execute(sql,args).fetchall()
