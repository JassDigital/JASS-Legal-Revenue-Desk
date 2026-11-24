import sqlite3

def migration_1(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE sources (
        source_id INTEGER PRIMARY KEY,
        source_name TEXT NOT NULL,
        source_type TEXT NOT NULL,
        official_url TEXT,
        publisher TEXT,
        authority_level TEXT,
        jurisdiction TEXT,
        last_verified TEXT,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE documents (
        document_id INTEGER PRIMARY KEY,
        document_title TEXT NOT NULL,
        document_type TEXT NOT NULL,
        original_filename TEXT,
        stored_path TEXT,
        file_hash TEXT,
        mime_type TEXT,
        page_count INTEGER,
        extraction_status TEXT NOT NULL DEFAULT 'not_started',
        source_id INTEGER REFERENCES sources(source_id),
        imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        extracted_text TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE legislation (
        legislation_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        short_title TEXT,
        act_number TEXT,
        year INTEGER,
        jurisdiction TEXT NOT NULL DEFAULT 'Haryana',
        state TEXT,
        legislation_type TEXT NOT NULL DEFAULT 'Act',
        enactment_date TEXT,
        commencement_date TEXT,
        repeal_date TEXT,
        current_status TEXT NOT NULL DEFAULT 'unverified',
        source_id INTEGER REFERENCES sources(source_id),
        document_id INTEGER REFERENCES documents(document_id),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE legislation_versions (
        version_id INTEGER PRIMARY KEY,
        legislation_id INTEGER NOT NULL REFERENCES legislation(legislation_id) ON DELETE CASCADE,
        version_number TEXT NOT NULL,
        effective_from TEXT,
        effective_to TEXT,
        amendment_reference TEXT,
        source_document_id INTEGER REFERENCES documents(document_id),
        consolidated_text TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified'
    );

    CREATE TABLE sections (
        section_id INTEGER PRIMARY KEY,
        legislation_id INTEGER NOT NULL REFERENCES legislation(legislation_id) ON DELETE CASCADE,
        section_number TEXT NOT NULL,
        section_title TEXT,
        section_text TEXT NOT NULL DEFAULT '',
        parent_section_id INTEGER REFERENCES sections(section_id),
        current_version_id INTEGER REFERENCES legislation_versions(version_id),
        UNIQUE(legislation_id, section_number)
    );

    CREATE TABLE amendments (
        amendment_id INTEGER PRIMARY KEY,
        legislation_id INTEGER NOT NULL REFERENCES legislation(legislation_id) ON DELETE CASCADE,
        amending_act TEXT NOT NULL,
        amendment_year INTEGER,
        affected_section TEXT,
        previous_text TEXT,
        amended_text TEXT,
        commencement_date TEXT,
        source_document_id INTEGER REFERENCES documents(document_id)
    );

    CREATE TABLE courts (
        court_id INTEGER PRIMARY KEY,
        court_name TEXT NOT NULL UNIQUE,
        court_level TEXT,
        jurisdiction TEXT,
        location TEXT
    );

    CREATE TABLE judgments (
        judgment_id INTEGER PRIMARY KEY,
        case_title TEXT NOT NULL,
        case_number TEXT,
        citation TEXT,
        court_id INTEGER REFERENCES courts(court_id),
        bench TEXT,
        judge_names TEXT,
        decision_date TEXT,
        disposition TEXT,
        case_type TEXT,
        full_text TEXT NOT NULL DEFAULT '',
        source_id INTEGER REFERENCES sources(source_id),
        official_url TEXT,
        document_id INTEGER REFERENCES documents(document_id),
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE legal_citations (
        citation_id INTEGER PRIMARY KEY,
        judgment_id INTEGER REFERENCES judgments(judgment_id) ON DELETE CASCADE,
        legislation_id INTEGER REFERENCES legislation(legislation_id),
        section_id INTEGER REFERENCES sections(section_id),
        cited_case_id INTEGER REFERENCES judgments(judgment_id),
        citation_context TEXT,
        citation_type TEXT
    );

    CREATE TABLE legal_cases (
        legal_case_id INTEGER PRIMARY KEY,
        case_title TEXT NOT NULL,
        case_number TEXT,
        court_name TEXT,
        case_category TEXT,
        district TEXT,
        tehsil TEXT,
        village TEXT,
        status TEXT NOT NULL DEFAULT 'research',
        filing_date TEXT,
        next_hearing_date TEXT,
        description TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE case_documents (
        id INTEGER PRIMARY KEY,
        legal_case_id INTEGER NOT NULL REFERENCES legal_cases(legal_case_id) ON DELETE CASCADE,
        document_id INTEGER NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
        document_role TEXT,
        remarks TEXT
    );

    CREATE TABLE research_notes (
        note_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        subject TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE case_law_status (
        id INTEGER PRIMARY KEY,
        judgment_id INTEGER NOT NULL REFERENCES judgments(judgment_id) ON DELETE CASCADE,
        subsequent_judgment_id INTEGER REFERENCES judgments(judgment_id),
        treatment_type TEXT NOT NULL,
        explanation TEXT,
        verification_source TEXT,
        verified_date TEXT
    );

    CREATE VIRTUAL TABLE legislation_fts USING fts5(
        title, short_title, content='legislation', content_rowid='legislation_id'
    );
    CREATE VIRTUAL TABLE sections_fts USING fts5(
        section_number, section_title, section_text,
        content='sections', content_rowid='section_id'
    );
    CREATE VIRTUAL TABLE judgments_fts USING fts5(
        case_title, citation, case_number, full_text,
        content='judgments', content_rowid='judgment_id'
    );
    CREATE VIRTUAL TABLE documents_fts USING fts5(
        document_title, extracted_text,
        content='documents', content_rowid='document_id'
    );
    CREATE VIRTUAL TABLE notes_fts USING fts5(
        title, content, subject,
        content='research_notes', content_rowid='note_id'
    );

    CREATE TRIGGER legislation_ai AFTER INSERT ON legislation BEGIN
      INSERT INTO legislation_fts(rowid,title,short_title) VALUES(new.legislation_id,new.title,new.short_title);
    END;
    CREATE TRIGGER legislation_ad AFTER DELETE ON legislation BEGIN
      INSERT INTO legislation_fts(legislation_fts,rowid,title,short_title) VALUES('delete',old.legislation_id,old.title,old.short_title);
    END;
    CREATE TRIGGER legislation_au AFTER UPDATE ON legislation BEGIN
      INSERT INTO legislation_fts(legislation_fts,rowid,title,short_title) VALUES('delete',old.legislation_id,old.title,old.short_title);
      INSERT INTO legislation_fts(rowid,title,short_title) VALUES(new.legislation_id,new.title,new.short_title);
    END;

    CREATE TRIGGER sections_ai AFTER INSERT ON sections BEGIN
      INSERT INTO sections_fts(rowid,section_number,section_title,section_text)
      VALUES(new.section_id,new.section_number,new.section_title,new.section_text);
    END;
    CREATE TRIGGER sections_ad AFTER DELETE ON sections BEGIN
      INSERT INTO sections_fts(sections_fts,rowid,section_number,section_title,section_text)
      VALUES('delete',old.section_id,old.section_number,old.section_title,old.section_text);
    END;
    CREATE TRIGGER sections_au AFTER UPDATE ON sections BEGIN
      INSERT INTO sections_fts(sections_fts,rowid,section_number,section_title,section_text)
      VALUES('delete',old.section_id,old.section_number,old.section_title,old.section_text);
      INSERT INTO sections_fts(rowid,section_number,section_title,section_text)
      VALUES(new.section_id,new.section_number,new.section_title,new.section_text);
    END;

    CREATE TRIGGER judgments_ai AFTER INSERT ON judgments BEGIN
      INSERT INTO judgments_fts(rowid,case_title,citation,case_number,full_text)
      VALUES(new.judgment_id,new.case_title,new.citation,new.case_number,new.full_text);
    END;
    CREATE TRIGGER judgments_ad AFTER DELETE ON judgments BEGIN
      INSERT INTO judgments_fts(judgments_fts,rowid,case_title,citation,case_number,full_text)
      VALUES('delete',old.judgment_id,old.case_title,old.citation,old.case_number,old.full_text);
    END;
    CREATE TRIGGER judgments_au AFTER UPDATE ON judgments BEGIN
      INSERT INTO judgments_fts(judgments_fts,rowid,case_title,citation,case_number,full_text)
      VALUES('delete',old.judgment_id,old.case_title,old.citation,old.case_number,old.full_text);
      INSERT INTO judgments_fts(rowid,case_title,citation,case_number,full_text)
      VALUES(new.judgment_id,new.case_title,new.citation,new.case_number,new.full_text);
    END;

    CREATE TRIGGER documents_ai AFTER INSERT ON documents BEGIN
      INSERT INTO documents_fts(rowid,document_title,extracted_text)
      VALUES(new.document_id,new.document_title,new.extracted_text);
    END;
    CREATE TRIGGER documents_ad AFTER DELETE ON documents BEGIN
      INSERT INTO documents_fts(documents_fts,rowid,document_title,extracted_text)
      VALUES('delete',old.document_id,old.document_title,old.extracted_text);
    END;
    CREATE TRIGGER documents_au AFTER UPDATE ON documents BEGIN
      INSERT INTO documents_fts(documents_fts,rowid,document_title,extracted_text)
      VALUES('delete',old.document_id,old.document_title,old.extracted_text);
      INSERT INTO documents_fts(rowid,document_title,extracted_text)
      VALUES(new.document_id,new.document_title,new.extracted_text);
    END;

    CREATE TRIGGER notes_ai AFTER INSERT ON research_notes BEGIN
      INSERT INTO notes_fts(rowid,title,content,subject)
      VALUES(new.note_id,new.title,new.content,new.subject);
    END;
    CREATE TRIGGER notes_ad AFTER DELETE ON research_notes BEGIN
      INSERT INTO notes_fts(notes_fts,rowid,title,content,subject)
      VALUES('delete',old.note_id,old.title,old.content,old.subject);
    END;
    CREATE TRIGGER notes_au AFTER UPDATE ON research_notes BEGIN
      INSERT INTO notes_fts(notes_fts,rowid,title,content,subject)
      VALUES('delete',old.note_id,old.title,old.content,old.subject);
      INSERT INTO notes_fts(rowid,title,content,subject)
      VALUES(new.note_id,new.title,new.content,new.subject);
    END;
    """)
