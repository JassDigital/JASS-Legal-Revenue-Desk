"""Data operations for the section reader, annotations, amendment timeline and topic workspace."""
TOPICS = [
    ("Mutation", "Mutation entries, objections, attestation, correction and appeal issues."),
    ("Jamabandi / Record of Rights", "Record of rights, periodic records, entries and evidentiary questions."),
    ("Inheritance / Succession", "Devolution, inheritance mutations, co-sharers and supporting records."),
    ("Partition", "Partition of holdings, co-sharer rights, procedure and revenue-estate notifications."),
    ("Girdawari", "Crop inspection, possession-related entries and correction proceedings."),
    ("Revenue Courts and Appeals", "Jurisdiction, appeals, revisions, review, limitation and procedural remedies."),
    ("Abadi Deh", "Abadi Deh ownership, survey, record of rights and SVAMITVA-related material."),
    ("Land Records Administration", "Haryana Land Records Manual, HALRIS, registers, instructions and circulars."),
]

def seed_topics(conn):
    for name, description in TOPICS:
        conn.execute("INSERT OR IGNORE INTO revenue_research_topics(topic_name,description) VALUES(?,?)",(name,description))
    conn.commit()

def materials(conn):
    return conn.execute("SELECT material_id,title,material_type,year,legal_status FROM revenue_law_materials ORDER BY year DESC,title").fetchall()

def sections(conn, material_id, query=""):
    sql = "SELECT * FROM revenue_law_sections WHERE material_id=?"
    args = [material_id]
    if query.strip():
        like = "%" + query.strip() + "%"
        sql += " AND (section_number LIKE ? OR heading LIKE ? OR section_text LIKE ? OR source_reference LIKE ?)"
        args.extend([like] * 4)
    sql += " ORDER BY section_number COLLATE NOCASE"
    return conn.execute(sql, args).fetchall()

def save_section(conn, material_id, section_number, heading, section_text, source_reference="", effective_from="", effective_to="", verification_status="unverified", section_id=None):
    if section_id:
        conn.execute("""UPDATE revenue_law_sections SET section_number=?,heading=?,section_text=?,source_reference=?,
            effective_from=?,effective_to=?,verification_status=?,updated_at=CURRENT_TIMESTAMP WHERE section_id=? AND material_id=?""",
            (section_number,heading,section_text,source_reference,effective_from or None,effective_to or None,verification_status,section_id,material_id))
    else:
        conn.execute("""INSERT INTO revenue_law_sections(material_id,section_number,heading,section_text,source_reference,effective_from,effective_to,verification_status)
            VALUES(?,?,?,?,?,?,?,?)""",(material_id,section_number,heading,section_text,source_reference,effective_from or None,effective_to or None,verification_status))
    conn.commit()

def annotations(conn, material_id):
    return conn.execute("""SELECT a.*,s.section_number FROM revenue_law_annotations a
        LEFT JOIN revenue_law_sections s ON s.section_id=a.section_id
        WHERE a.material_id=? ORDER BY a.updated_at DESC,a.annotation_id DESC""",(material_id,)).fetchall()

def save_annotation(conn, material_id, section_id, annotation_type, title, content, tags=""):
    conn.execute("""INSERT INTO revenue_law_annotations(material_id,section_id,annotation_type,title,content,tags)
        VALUES(?,?,?,?,?,?)""",(material_id,section_id,annotation_type,title,content,tags))
    conn.commit()

def amendments(conn, material_id):
    return conn.execute("""SELECT a.*,m.title AS amending_title FROM revenue_law_amendments a
        LEFT JOIN revenue_law_materials m ON m.material_id=a.amendment_material_id
        WHERE a.material_id=? ORDER BY COALESCE(a.effective_from,'') DESC,a.amendment_id DESC""",(material_id,)).fetchall()

def save_amendment(conn, material_id, affected_section, amendment_title, amendment_material_id, effective_from, effective_to, summary, source_reference, verification_status):
    conn.execute("""INSERT INTO revenue_law_amendments(material_id,affected_section,amendment_title,amendment_material_id,
        effective_from,effective_to,summary,source_reference,verification_status) VALUES(?,?,?,?,?,?,?,?,?)""",
        (material_id,affected_section,amendment_title,amendment_material_id or None,effective_from or None,effective_to or None,summary,source_reference,verification_status))
    conn.commit()

def topic_rows(conn):
    return conn.execute("""SELECT t.topic_id,t.topic_name,t.description,COUNT(l.material_id) AS material_count
        FROM revenue_research_topics t LEFT JOIN revenue_topic_material_links l ON l.topic_id=t.topic_id
        GROUP BY t.topic_id ORDER BY t.topic_name""").fetchall()

def topic_materials(conn, topic_id):
    return conn.execute("""SELECT m.* FROM revenue_law_materials m JOIN revenue_topic_material_links l
        ON l.material_id=m.material_id WHERE l.topic_id=? ORDER BY m.year DESC,m.title""",(topic_id,)).fetchall()

def link_topic_material(conn, topic_id, material_id, notes=""):
    conn.execute("INSERT OR IGNORE INTO revenue_topic_material_links(topic_id,material_id,notes) VALUES(?,?,?)",(topic_id,material_id,notes))
    conn.commit()

def material_links(conn, material_id):
    return conn.execute("""SELECT l.*,m.title AS target_title FROM revenue_law_material_links l
        JOIN revenue_law_materials m ON m.material_id=l.target_material_id
        WHERE l.source_material_id=? ORDER BY m.title""",(material_id,)).fetchall()

def save_material_link(conn, source_id, target_id, relationship, notes, verification_status):
    conn.execute("""INSERT OR IGNORE INTO revenue_law_material_links(source_material_id,target_material_id,relationship_type,notes,verification_status)
        VALUES(?,?,?,?,?)""",(source_id,target_id,relationship,notes,verification_status))
    conn.commit()
