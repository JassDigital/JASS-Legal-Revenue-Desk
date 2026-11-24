def load_sample_data(conn):
    """Insert clearly labelled demonstration records once; no claim of legal authority."""
    existing = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    if existing:
        return
    conn.execute("""
        INSERT INTO sources(source_name,source_type,publisher,authority_level,jurisdiction,notes)
        VALUES(?,?,?,?,?,?)
    """, (
        "JASS Demonstration Data", "sample", "JASS Digital Lab",
        "demonstration_only", "Haryana",
        "Synthetic sample records. Not an official legal source."
    ))
    source_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO legislation(title,short_title,year,jurisdiction,legislation_type,current_status,source_id)
        VALUES(?,?,?,?,?,?,?)
    """, (
        "Demonstration Haryana Land Revenue Research Record",
        "Sample Revenue Record", 2026, "Haryana", "Demonstration",
        "sample_only", source_id
    ))
    legislation_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO sections(legislation_id,section_number,section_title,section_text)
        VALUES(?,?,?,?)
    """, (
        legislation_id, "DEMO-1", "Sample search provision",
        "This is synthetic demonstration text for testing full-text search. It is not legislation."
    ))
    conn.execute("""
        INSERT INTO judgments(case_title,case_number,citation,case_type,full_text,source_id,verification_status)
        VALUES(?,?,?,?,?,?,?)
    """, (
        "Demonstration v. Sample", "DEMO/2026/001", "DEMO-CITATION-ONLY",
        "Demonstration", "Synthetic judgment text for testing legal search. Not a real case or precedent.",
        source_id, "sample_only"
    ))
    conn.execute("""
        INSERT INTO research_notes(title,content,subject)
        VALUES(?,?,?)
    """, (
        "Getting started with revenue research",
        "Use this note to test search. Replace demonstration content with verified research.",
        "Training"
    ))
    conn.commit()
