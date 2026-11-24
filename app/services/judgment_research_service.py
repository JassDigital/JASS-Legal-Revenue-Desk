class JudgmentResearchService:
    """Research operations over locally stored judgments. Does not claim live coverage."""
    def __init__(self, conn):
        self.conn=conn

    @staticmethod
    def _fts_phrase(query):
        cleaned=(query or "").strip().replace('"','""')
        return f'"{cleaned}"' if cleaned else ""

    def search(self, query="", court="All", year="", topic="All",
               verification="All", limit=200):
        # FTS for substantive searches; structured filters are applied to returned IDs.
        if not (query or court!="All" or year or topic!="All" or verification!="All"):
            return []
        ids=None
        term=self._fts_phrase(query)
        if term:
            try:
                rows=self.conn.execute("""
                    SELECT rowid FROM judgment_research_fts
                    WHERE judgment_research_fts MATCH ? LIMIT ?
                """,(term,limit*5)).fetchall()
                ids={r["rowid"] for r in rows}
            except Exception:
                ids=set()
        sql="SELECT j.* FROM judgments j WHERE 1=1"; args=[]
        if ids is not None:
            if not ids: return []
            placeholders=",".join("?" for _ in ids)
            sql += f" AND j.judgment_id IN ({placeholders})"
            args.extend(ids)
        if court!="All": sql+=" AND j.court_name=?"; args.append(court)
        if year: sql+=" AND substr(j.decision_date,1,4)=?"; args.append(str(year))
        if verification!="All": sql+=" AND j.verification_status=?"; args.append(verification)
        if topic!="All":
            sql+=""" AND EXISTS(SELECT 1 FROM judgment_topics t WHERE t.judgment_id=j.judgment_id
                      AND t.normalized_topic=?)"""
            args.append(topic.casefold())
        sql+=" ORDER BY j.decision_date DESC,j.judgment_id DESC LIMIT ?"; args.append(limit)
        return self.conn.execute(sql,args).fetchall()

    def add_topic(self, judgment_id, topic):
        topic=topic.strip()
        if not topic: raise ValueError("Topic cannot be blank.")
        normalized=topic.casefold()
        self.conn.execute("""INSERT OR IGNORE INTO judgment_topics(judgment_id,topic,normalized_topic)
                             VALUES(?,?,?)""",(judgment_id,topic,normalized))
        # Keep topics in the FTS searchable keyword field too.
        row=self.conn.execute("SELECT subject_keywords FROM judgments WHERE judgment_id=?",(judgment_id,)).fetchone()
        if not row: raise ValueError("Judgment not found.")
        words=[x.strip() for x in (row["subject_keywords"] or "").split(";") if x.strip()]
        if topic.casefold() not in {x.casefold() for x in words}:
            words.append(topic)
            self.conn.execute("UPDATE judgments SET subject_keywords=? WHERE judgment_id=?",
                              ("; ".join(words),judgment_id))
        self.conn.commit()

    def add_statutory_reference(self, judgment_id, act_name, section_number,
                                context="", verification_status="unverified"):
        if not act_name.strip() or not section_number.strip():
            raise ValueError("Act name and section number are required.")
        self.conn.execute("""INSERT OR IGNORE INTO judgment_statutory_references
            (judgment_id,act_name,section_number,reference_context,verification_status)
            VALUES(?,?,?,?,?)""",(judgment_id,act_name.strip(),section_number.strip(),context,verification_status))
        self.conn.commit()

    def statutory_references(self, judgment_id):
        return self.conn.execute("""SELECT * FROM judgment_statutory_references
            WHERE judgment_id=? ORDER BY act_name,section_number""",(judgment_id,)).fetchall()

    def add_relation(self, source_id, target_id, relation_type, notes="",
                     verification_status="unverified"):
        if source_id==target_id: raise ValueError("A judgment cannot be related to itself.")
        self.conn.execute("""INSERT OR IGNORE INTO judgment_relations
            (source_judgment_id,target_judgment_id,relation_type,notes,verification_status)
            VALUES(?,?,?,?,?)""",(source_id,target_id,relation_type,notes,verification_status))
        self.conn.commit()

    def related(self, judgment_id):
        return self.conn.execute("""
            SELECT r.*, j.case_title AS related_title, j.citation AS related_citation,
                   j.court_name AS related_court, j.decision_date AS related_date
            FROM judgment_relations r
            JOIN judgments j ON j.judgment_id=r.target_judgment_id
            WHERE r.source_judgment_id=?
            ORDER BY j.decision_date DESC
        """,(judgment_id,)).fetchall()
