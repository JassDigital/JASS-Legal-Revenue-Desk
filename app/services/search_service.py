class SearchService:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _safe_fts_query(query: str) -> str:
        # Treat the user's input as a phrase, avoiding accidental FTS syntax errors.
        cleaned = query.strip().replace('"', '""')
        return f'"{cleaned}"' if cleaned else ""

    def search(self, query: str, limit: int = 100):
        term = self._safe_fts_query(query)
        if not term:
            return []
        results = []
        searches = [
            ("Legislation", """
                SELECT l.title AS title, COALESCE(l.short_title,'') AS detail,
                       snippet(legislation_fts,0,'[',']','…',18) AS excerpt,
                       l.legislation_id AS item_id
                FROM legislation_fts JOIN legislation l ON l.legislation_id=legislation_fts.rowid
                WHERE legislation_fts MATCH ? LIMIT ?
            """),
            ("Section", """
                SELECT s.section_number || ' — ' || COALESCE(s.section_title,'') AS title,
                       l.title AS detail,
                       snippet(sections_fts,2,'[',']','…',18) AS excerpt,
                       s.section_id AS item_id
                FROM sections_fts JOIN sections s ON s.section_id=sections_fts.rowid
                JOIN legislation l ON l.legislation_id=s.legislation_id
                WHERE sections_fts MATCH ? LIMIT ?
            """),
            ("Judgment", """
                SELECT j.case_title AS title, COALESCE(j.citation,j.case_number,'') AS detail,
                       snippet(judgments_fts,3,'[',']','…',18) AS excerpt,
                       j.judgment_id AS item_id
                FROM judgments_fts JOIN judgments j ON j.judgment_id=judgments_fts.rowid
                WHERE judgments_fts MATCH ? LIMIT ?
            """),
            ("Document", """
                SELECT d.document_title AS title, d.document_type AS detail,
                       snippet(documents_fts,1,'[',']','…',18) AS excerpt,
                       d.document_id AS item_id
                FROM documents_fts JOIN documents d ON d.document_id=documents_fts.rowid
                WHERE documents_fts MATCH ? LIMIT ?
            """),
            ("Research note", """
                SELECT n.title AS title, COALESCE(n.subject,'') AS detail,
                       snippet(notes_fts,1,'[',']','…',18) AS excerpt,
                       n.note_id AS item_id
                FROM notes_fts JOIN research_notes n ON n.note_id=notes_fts.rowid
                WHERE notes_fts MATCH ? LIMIT ?
            """),
        ]
        for kind, sql in searches:
            try:
                rows = self.conn.execute(sql, (term, limit)).fetchall()
                for row in rows:
                    results.append({
                        "kind": kind, "title": row["title"],
                        "detail": row["detail"], "excerpt": row["excerpt"],
                        "item_id": row["item_id"]
                    })
            except Exception:
                # A malformed or unsupported query in one index should not crash the UI.
                continue
        return results[:limit]
