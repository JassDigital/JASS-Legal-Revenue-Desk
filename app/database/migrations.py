import sqlite3
CURRENT_SCHEMA_VERSION = 16

def migrate(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    row = conn.execute("SELECT MAX(version) AS v FROM schema_migrations").fetchone()
    version = row["v"] or 0
    if version < 1:
        from app.database.schema_v1 import migration_1
        migration_1(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (1)")
        conn.commit()
        version = 1
    if version < 2:
        conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_legislation_jurisdiction_year ON legislation(jurisdiction, year);
        CREATE INDEX IF NOT EXISTS idx_judgments_decision_date ON judgments(decision_date);
        CREATE INDEX IF NOT EXISTS idx_judgments_citation ON judgments(citation);
        CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
        CREATE TABLE IF NOT EXISTS document_import_log (
            import_id INTEGER PRIMARY KEY,
            document_id INTEGER REFERENCES documents(document_id),
            original_path TEXT NOT NULL,
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            result TEXT NOT NULL,
            message TEXT
        );
        CREATE TABLE IF NOT EXISTS source_verification_log (
            verification_id INTEGER PRIMARY KEY,
            source_id INTEGER REFERENCES sources(source_id),
            document_id INTEGER REFERENCES documents(document_id),
            verification_status TEXT NOT NULL,
            verified_by TEXT,
            verified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            verification_notes TEXT
        );
        """)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (2)")
        conn.commit()
        version = 2
    if version < 3:
        _migration_3(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (3)")
        conn.commit()
        version = 3
    if version < 4:
        _migration_4(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (4)")
        conn.commit()
        version = 4
    if version < 5:
        _migration_5(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (5)")
        conn.commit()
        version = 5
    if version < 6:
        _migration_6(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (6)")
        conn.commit()
        version = 6
    if version < 7:
        _migration_7(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (7)")
        conn.commit()
        version = 7
    if version < 8:
        _migration_8(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (8)")
        conn.commit()
        version = 8
    if version < 9:
        _migration_9(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (9)")
        conn.commit()
        version = 9
    if version < 10:
        _migration_10(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (10)")
        conn.commit()
        version = 10
    if version < 11:
        _migration_11(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (11)")
        conn.commit()
        version = 11
    if version < 12:
        _migration_12(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (12)")
        conn.commit()
        version = 12
    if version < 13:
        _migration_13(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (13)")
        conn.commit()
        version = 13
    if version < 14:
        _migration_14(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (14)")
        conn.commit()
        version = 14
    if version < 15:
        _migration_15(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (15)")
        conn.commit()
        version = 15
    if version < 16:
        _migration_16(conn)
        conn.execute("INSERT INTO schema_migrations(version) VALUES (16)")
        conn.commit()

def _migration_3(conn):
    existing = {r["name"] for r in conn.execute("PRAGMA table_info(judgments)")}
    for name, declaration in [
        ("court_name", "TEXT"),
        ("petitioner", "TEXT"),
        ("respondent", "TEXT"),
        ("subject_keywords", "TEXT NOT NULL DEFAULT ''"),
        ("paragraph_reference", "TEXT"),
    ]:
        if name not in existing:
            conn.execute(f"ALTER TABLE judgments ADD COLUMN {name} {declaration}")

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS judgment_topics (
        topic_id INTEGER PRIMARY KEY,
        judgment_id INTEGER NOT NULL REFERENCES judgments(judgment_id) ON DELETE CASCADE,
        topic TEXT NOT NULL,
        normalized_topic TEXT NOT NULL,
        UNIQUE(judgment_id, normalized_topic)
    );
    CREATE INDEX IF NOT EXISTS idx_judgment_topics_normalized ON judgment_topics(normalized_topic);

    CREATE TABLE IF NOT EXISTS judgment_statutory_references (
        reference_id INTEGER PRIMARY KEY,
        judgment_id INTEGER NOT NULL REFERENCES judgments(judgment_id) ON DELETE CASCADE,
        act_name TEXT NOT NULL,
        section_number TEXT NOT NULL,
        reference_context TEXT,
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        UNIQUE(judgment_id, act_name, section_number)
    );

    CREATE TABLE IF NOT EXISTS judgment_relations (
        relation_id INTEGER PRIMARY KEY,
        source_judgment_id INTEGER NOT NULL REFERENCES judgments(judgment_id) ON DELETE CASCADE,
        target_judgment_id INTEGER NOT NULL REFERENCES judgments(judgment_id) ON DELETE CASCADE,
        relation_type TEXT NOT NULL,
        notes TEXT,
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK(source_judgment_id <> target_judgment_id),
        UNIQUE(source_judgment_id, target_judgment_id, relation_type)
    );

    CREATE INDEX IF NOT EXISTS idx_judgments_court_name ON judgments(court_name);
    CREATE INDEX IF NOT EXISTS idx_judgments_decision_year ON judgments(substr(decision_date,1,4));

    CREATE VIRTUAL TABLE IF NOT EXISTS judgment_research_fts USING fts5(
        case_title, case_number, citation, court_name, petitioner, respondent,
        judge_names, subject_keywords, full_text
    );

    INSERT INTO judgment_research_fts(
        rowid,case_title,case_number,citation,court_name,petitioner,respondent,
        judge_names,subject_keywords,full_text
    )
    SELECT judgment_id,case_title,COALESCE(case_number,''),COALESCE(citation,''),
        COALESCE(court_name,''),COALESCE(petitioner,''),COALESCE(respondent,''),
        COALESCE(judge_names,''),COALESCE(subject_keywords,''),COALESCE(full_text,'')
    FROM judgments;

    CREATE TRIGGER IF NOT EXISTS judgment_research_ai AFTER INSERT ON judgments BEGIN
      INSERT INTO judgment_research_fts(rowid,case_title,case_number,citation,court_name,
        petitioner,respondent,judge_names,subject_keywords,full_text)
      VALUES(new.judgment_id,new.case_title,COALESCE(new.case_number,''),COALESCE(new.citation,''),
        COALESCE(new.court_name,''),COALESCE(new.petitioner,''),COALESCE(new.respondent,''),
        COALESCE(new.judge_names,''),COALESCE(new.subject_keywords,''),COALESCE(new.full_text,''));
    END;

    CREATE TRIGGER IF NOT EXISTS judgment_research_ad AFTER DELETE ON judgments BEGIN
      DELETE FROM judgment_research_fts WHERE rowid=old.judgment_id;
    END;

    CREATE TRIGGER IF NOT EXISTS judgment_research_au AFTER UPDATE ON judgments BEGIN
      DELETE FROM judgment_research_fts WHERE rowid=old.judgment_id;
      INSERT INTO judgment_research_fts(rowid,case_title,case_number,citation,court_name,
        petitioner,respondent,judge_names,subject_keywords,full_text)
      VALUES(new.judgment_id,new.case_title,COALESCE(new.case_number,''),COALESCE(new.citation,''),
        COALESCE(new.court_name,''),COALESCE(new.petitioner,''),COALESCE(new.respondent,''),
        COALESCE(new.judge_names,''),COALESCE(new.subject_keywords,''),COALESCE(new.full_text,''));
    END;
    """)


def _migration_4(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS online_import_log (
        online_import_id INTEGER PRIMARY KEY,
        source_id INTEGER REFERENCES sources(source_id),
        document_id INTEGER REFERENCES documents(document_id),
        requested_url TEXT NOT NULL,
        final_url TEXT NOT NULL,
        fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        http_status INTEGER,
        content_type TEXT,
        content_length INTEGER,
        sha256 TEXT NOT NULL,
        result TEXT NOT NULL,
        notes TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_online_import_hash ON online_import_log(sha256);
    CREATE INDEX IF NOT EXISTS idx_online_import_source ON online_import_log(source_id);
    """)


def _migration_5(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_law_materials (
        material_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        material_type TEXT NOT NULL,
        jurisdiction TEXT NOT NULL DEFAULT 'Haryana',
        year INTEGER,
        act_number TEXT,
        publication_date TEXT,
        effective_date TEXT,
        subject_tags TEXT NOT NULL DEFAULT '',
        description TEXT NOT NULL DEFAULT '',
        source_name TEXT,
        source_url TEXT,
        source_classification TEXT NOT NULL DEFAULT 'needs_source_review',
        legal_status TEXT NOT NULL DEFAULT 'needs_legal_verification',
        verification_notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(title, year, act_number)
    );
    CREATE INDEX IF NOT EXISTS idx_revenue_material_type ON revenue_law_materials(material_type);
    CREATE INDEX IF NOT EXISTS idx_revenue_material_year ON revenue_law_materials(year);
    CREATE INDEX IF NOT EXISTS idx_revenue_material_status ON revenue_law_materials(legal_status);
    CREATE VIRTUAL TABLE IF NOT EXISTS revenue_law_materials_fts USING fts5(
        title, material_type, jurisdiction, act_number, subject_tags, description,
        content='revenue_law_materials', content_rowid='material_id'
    );
    CREATE TRIGGER IF NOT EXISTS revenue_material_ai AFTER INSERT ON revenue_law_materials BEGIN
      INSERT INTO revenue_law_materials_fts(rowid,title,material_type,jurisdiction,act_number,subject_tags,description)
      VALUES(new.material_id,new.title,new.material_type,new.jurisdiction,new.act_number,new.subject_tags,new.description);
    END;
    CREATE TRIGGER IF NOT EXISTS revenue_material_ad AFTER DELETE ON revenue_law_materials BEGIN
      INSERT INTO revenue_law_materials_fts(revenue_law_materials_fts,rowid,title,material_type,jurisdiction,act_number,subject_tags,description)
      VALUES('delete',old.material_id,old.title,old.material_type,old.jurisdiction,old.act_number,old.subject_tags,old.description);
    END;
    CREATE TRIGGER IF NOT EXISTS revenue_material_au AFTER UPDATE ON revenue_law_materials BEGIN
      INSERT INTO revenue_law_materials_fts(revenue_law_materials_fts,rowid,title,material_type,jurisdiction,act_number,subject_tags,description)
      VALUES('delete',old.material_id,old.title,old.material_type,old.jurisdiction,old.act_number,old.subject_tags,old.description);
      INSERT INTO revenue_law_materials_fts(rowid,title,material_type,jurisdiction,act_number,subject_tags,description)
      VALUES(new.material_id,new.title,new.material_type,new.jurisdiction,new.act_number,new.subject_tags,new.description);
    END;
    """)


def _migration_6(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_law_sections (
        section_id INTEGER PRIMARY KEY,
        material_id INTEGER NOT NULL REFERENCES revenue_law_materials(material_id) ON DELETE CASCADE,
        section_number TEXT NOT NULL,
        heading TEXT,
        section_text TEXT NOT NULL DEFAULT '',
        source_reference TEXT,
        effective_from TEXT,
        effective_to TEXT,
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(material_id, section_number)
    );
    CREATE INDEX IF NOT EXISTS idx_revenue_sections_material ON revenue_law_sections(material_id, section_number);

    CREATE TABLE IF NOT EXISTS revenue_law_annotations (
        annotation_id INTEGER PRIMARY KEY,
        material_id INTEGER NOT NULL REFERENCES revenue_law_materials(material_id) ON DELETE CASCADE,
        section_id INTEGER REFERENCES revenue_law_sections(section_id) ON DELETE CASCADE,
        annotation_type TEXT NOT NULL DEFAULT 'Research note',
        title TEXT NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        tags TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_revenue_annotations_material ON revenue_law_annotations(material_id);

    CREATE TABLE IF NOT EXISTS revenue_law_amendments (
        amendment_id INTEGER PRIMARY KEY,
        material_id INTEGER NOT NULL REFERENCES revenue_law_materials(material_id) ON DELETE CASCADE,
        affected_section TEXT NOT NULL,
        amendment_title TEXT NOT NULL,
        amendment_material_id INTEGER REFERENCES revenue_law_materials(material_id),
        effective_from TEXT,
        effective_to TEXT,
        summary TEXT NOT NULL DEFAULT '',
        source_reference TEXT,
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_revenue_amendments_material ON revenue_law_amendments(material_id, affected_section);

    CREATE TABLE IF NOT EXISTS revenue_law_material_links (
        link_id INTEGER PRIMARY KEY,
        source_material_id INTEGER NOT NULL REFERENCES revenue_law_materials(material_id) ON DELETE CASCADE,
        target_material_id INTEGER NOT NULL REFERENCES revenue_law_materials(material_id) ON DELETE CASCADE,
        relationship_type TEXT NOT NULL,
        notes TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK(source_material_id <> target_material_id),
        UNIQUE(source_material_id,target_material_id,relationship_type)
    );

    CREATE TABLE IF NOT EXISTS revenue_research_topics (
        topic_id INTEGER PRIMARY KEY,
        topic_name TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS revenue_topic_material_links (
        topic_id INTEGER NOT NULL REFERENCES revenue_research_topics(topic_id) ON DELETE CASCADE,
        material_id INTEGER NOT NULL REFERENCES revenue_law_materials(material_id) ON DELETE CASCADE,
        notes TEXT NOT NULL DEFAULT '',
        PRIMARY KEY(topic_id,material_id)
    );
    """)


def _migration_7(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_cases (
        case_id INTEGER PRIMARY KEY,
        case_title TEXT NOT NULL,
        case_type TEXT NOT NULL DEFAULT 'Other',
        case_number TEXT,
        authority TEXT,
        district TEXT,
        tehsil TEXT,
        village TEXT,
        filing_date TEXT,
        status TEXT NOT NULL DEFAULT 'Preparing',
        next_hearing_date TEXT,
        priority TEXT NOT NULL DEFAULT 'Normal',
        case_summary TEXT NOT NULL DEFAULT '',
        strategy_notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_revenue_cases_status ON revenue_cases(status);
    CREATE INDEX IF NOT EXISTS idx_revenue_cases_next_date ON revenue_cases(next_hearing_date);

    CREATE TABLE IF NOT EXISTS revenue_case_parties (
        party_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        party_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Other',
        address TEXT,
        contact_notes TEXT,
        representative TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_case_parties_case ON revenue_case_parties(case_id);

    CREATE TABLE IF NOT EXISTS revenue_case_properties (
        property_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        village TEXT,
        tehsil TEXT,
        district TEXT,
        hadbast_number TEXT,
        jamabandi_year TEXT,
        khata_number TEXT,
        khatauni_number TEXT,
        khasra_numbers TEXT,
        area TEXT,
        ownership_share TEXT,
        land_description TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_case_properties_case ON revenue_case_properties(case_id);

    CREATE TABLE IF NOT EXISTS revenue_case_events (
        event_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        event_date TEXT,
        event_type TEXT NOT NULL DEFAULT 'Chronology',
        title TEXT NOT NULL,
        details TEXT NOT NULL DEFAULT '',
        next_action TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_case_events_date ON revenue_case_events(case_id,event_date);

    CREATE TABLE IF NOT EXISTS revenue_case_evidence (
        evidence_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        document_id INTEGER REFERENCES documents(document_id) ON DELETE SET NULL,
        evidence_title TEXT NOT NULL,
        evidence_type TEXT NOT NULL DEFAULT 'Other',
        document_reference TEXT,
        relevance_notes TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_case_evidence_case ON revenue_case_evidence(case_id);

    CREATE TABLE IF NOT EXISTS revenue_case_issues (
        issue_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        issue_title TEXT NOT NULL,
        facts TEXT NOT NULL DEFAULT '',
        legal_question TEXT NOT NULL DEFAULT '',
        proposed_argument TEXT NOT NULL DEFAULT '',
        relevant_law TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Open',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_case_issues_case ON revenue_case_issues(case_id);
    """)


def _migration_8(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_case_drafts (
        draft_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        draft_type TEXT NOT NULL DEFAULT 'Other',
        title TEXT NOT NULL,
        body TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Working',
        version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_case_drafts_case ON revenue_case_drafts(case_id);
    CREATE TABLE IF NOT EXISTS revenue_case_evidence_links (
        link_id INTEGER PRIMARY KEY,
        evidence_id INTEGER NOT NULL REFERENCES revenue_case_evidence(evidence_id) ON DELETE CASCADE,
        party_id INTEGER REFERENCES revenue_case_parties(party_id) ON DELETE CASCADE,
        issue_id INTEGER REFERENCES revenue_case_issues(issue_id) ON DELETE CASCADE,
        link_note TEXT NOT NULL DEFAULT '',
        CHECK (party_id IS NOT NULL OR issue_id IS NOT NULL),
        UNIQUE(evidence_id, party_id, issue_id)
    );
    CREATE INDEX IF NOT EXISTS idx_evidence_links_evidence ON revenue_case_evidence_links(evidence_id);
    CREATE TABLE IF NOT EXISTS revenue_case_report_log (
        report_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        report_type TEXT NOT NULL,
        exported_path TEXT,
        exported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)


def _migration_9(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_record_sets (
        record_set_id INTEGER PRIMARY KEY,
        case_id INTEGER REFERENCES revenue_cases(case_id) ON DELETE SET NULL,
        record_type TEXT NOT NULL DEFAULT 'Jamabandi',
        record_year TEXT NOT NULL,
        district TEXT,
        tehsil TEXT,
        village TEXT NOT NULL,
        hadbast_number TEXT,
        estate_name TEXT,
        source_reference TEXT,
        source_document_id INTEGER REFERENCES documents(document_id) ON DELETE SET NULL,
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_record_sets_village_year ON revenue_record_sets(village,record_year);
    CREATE TABLE IF NOT EXISTS revenue_record_entries (
        entry_id INTEGER PRIMARY KEY,
        record_set_id INTEGER NOT NULL REFERENCES revenue_record_sets(record_set_id) ON DELETE CASCADE,
        khewat_number TEXT,
        khata_number TEXT,
        khatauni_number TEXT,
        khasra_number TEXT NOT NULL,
        owner_name TEXT NOT NULL,
        parent_name TEXT,
        area_value REAL,
        area_unit TEXT NOT NULL DEFAULT 'acre',
        share_numerator INTEGER,
        share_denominator INTEGER,
        entry_notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_record_entries_khasra ON revenue_record_entries(khasra_number);
    CREATE INDEX IF NOT EXISTS idx_record_entries_owner ON revenue_record_entries(owner_name);
    CREATE TABLE IF NOT EXISTS revenue_mutation_records (
        mutation_id INTEGER PRIMARY KEY,
        record_set_id INTEGER REFERENCES revenue_record_sets(record_set_id) ON DELETE SET NULL,
        case_id INTEGER REFERENCES revenue_cases(case_id) ON DELETE SET NULL,
        mutation_number TEXT NOT NULL,
        mutation_date TEXT,
        mutation_type TEXT NOT NULL DEFAULT 'Other',
        khasra_numbers TEXT,
        from_party TEXT,
        to_party TEXT,
        area_value REAL,
        area_unit TEXT NOT NULL DEFAULT 'acre',
        share_numerator INTEGER,
        share_denominator INTEGER,
        status TEXT NOT NULL DEFAULT 'Unverified',
        source_reference TEXT,
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_mutation_number ON revenue_mutation_records(mutation_number);
    CREATE INDEX IF NOT EXISTS idx_mutation_date ON revenue_mutation_records(mutation_date);
    """)


def _migration_10(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_partition_plans (
        plan_id INTEGER PRIMARY KEY,
        case_id INTEGER REFERENCES revenue_cases(case_id) ON DELETE SET NULL,
        record_set_id INTEGER NOT NULL REFERENCES revenue_record_sets(record_set_id) ON DELETE CASCADE,
        plan_title TEXT NOT NULL,
        plan_status TEXT NOT NULL DEFAULT 'Working',
        basis_notes TEXT NOT NULL DEFAULT '',
        assumptions TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_partition_plans_record_set ON revenue_partition_plans(record_set_id);
    CREATE TABLE IF NOT EXISTS revenue_partition_allocations (
        allocation_id INTEGER PRIMARY KEY,
        plan_id INTEGER NOT NULL REFERENCES revenue_partition_plans(plan_id) ON DELETE CASCADE,
        khasra_number TEXT NOT NULL,
        co_sharer_name TEXT NOT NULL,
        proposed_area REAL NOT NULL DEFAULT 0,
        area_unit TEXT NOT NULL DEFAULT 'acre',
        proposed_share_numerator INTEGER,
        proposed_share_denominator INTEGER,
        location_or_quality_notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK(proposed_area >= 0),
        CHECK((proposed_share_numerator IS NULL AND proposed_share_denominator IS NULL)
           OR (proposed_share_numerator >= 0 AND proposed_share_denominator > 0))
    );
    CREATE INDEX IF NOT EXISTS idx_partition_allocations_plan ON revenue_partition_allocations(plan_id);
    """)


def _migration_11(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_proceeding_plans (
        proceeding_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        proceeding_type TEXT NOT NULL,
        forum_name TEXT,
        case_reference TEXT,
        start_date TEXT,
        current_stage TEXT NOT NULL DEFAULT 'Preparation',
        status TEXT NOT NULL DEFAULT 'Working',
        limitation_start_date TEXT,
        limitation_period_note TEXT NOT NULL DEFAULT '',
        limitation_source_reference TEXT NOT NULL DEFAULT '',
        limitation_reviewed_by TEXT,
        limitation_reviewed_date TEXT,
        limitation_due_date TEXT,
        limitation_caveat TEXT NOT NULL DEFAULT '',
        strategy_notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_proceeding_case ON revenue_proceeding_plans(case_id);
    CREATE TABLE IF NOT EXISTS revenue_proceeding_steps (
        step_id INTEGER PRIMARY KEY,
        proceeding_id INTEGER NOT NULL REFERENCES revenue_proceeding_plans(proceeding_id) ON DELETE CASCADE,
        step_order INTEGER NOT NULL DEFAULT 0,
        step_title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        step_status TEXT NOT NULL DEFAULT 'Not started',
        target_date TEXT,
        completed_date TEXT,
        responsible_person TEXT,
        source_reference TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_proceeding_steps ON revenue_proceeding_steps(proceeding_id,step_order);
    CREATE TABLE IF NOT EXISTS revenue_proceeding_events (
        event_id INTEGER PRIMARY KEY,
        proceeding_id INTEGER NOT NULL REFERENCES revenue_proceeding_plans(proceeding_id) ON DELETE CASCADE,
        event_date TEXT,
        event_type TEXT NOT NULL DEFAULT 'Other',
        title TEXT NOT NULL,
        details TEXT NOT NULL DEFAULT '',
        next_action TEXT NOT NULL DEFAULT '',
        deadline_date TEXT,
        source_reference TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Open',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_proceeding_events ON revenue_proceeding_events(proceeding_id,event_date);
    """)


def _migration_12(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS legal_source_records (
        source_record_id INTEGER PRIMARY KEY,
        material_id INTEGER REFERENCES revenue_law_materials(material_id) ON DELETE SET NULL,
        section_id INTEGER REFERENCES revenue_law_sections(section_id) ON DELETE SET NULL,
        judgment_id INTEGER REFERENCES judgments(judgment_id) ON DELETE SET NULL,
        document_id INTEGER REFERENCES documents(document_id) ON DELETE SET NULL,
        source_title TEXT NOT NULL,
        source_type TEXT NOT NULL DEFAULT 'Other',
        publisher TEXT NOT NULL DEFAULT '',
        jurisdiction TEXT NOT NULL DEFAULT 'Haryana',
        source_url TEXT NOT NULL DEFAULT '',
        source_identifier TEXT NOT NULL DEFAULT '',
        publication_date TEXT,
        retrieval_date TEXT,
        effective_from TEXT,
        effective_to TEXT,
        officiality TEXT NOT NULL DEFAULT 'unknown',
        legal_status TEXT NOT NULL DEFAULT 'unverified',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        verified_by TEXT NOT NULL DEFAULT '',
        verified_date TEXT,
        hash_sha256 TEXT NOT NULL DEFAULT '',
        source_snapshot_path TEXT NOT NULL DEFAULT '',
        verification_notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_legal_source_status ON legal_source_records(verification_status,legal_status);
    CREATE INDEX IF NOT EXISTS idx_legal_source_title ON legal_source_records(source_title);
    CREATE TABLE IF NOT EXISTS legal_source_versions (
        source_version_id INTEGER PRIMARY KEY,
        source_record_id INTEGER NOT NULL REFERENCES legal_source_records(source_record_id) ON DELETE CASCADE,
        version_label TEXT NOT NULL,
        instrument_reference TEXT NOT NULL DEFAULT '',
        effective_from TEXT,
        effective_to TEXT,
        publication_date TEXT,
        source_reference TEXT NOT NULL DEFAULT '',
        change_summary TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_legal_source_versions ON legal_source_versions(source_record_id,effective_from);
    CREATE TABLE IF NOT EXISTS legal_citation_links (
        citation_link_id INTEGER PRIMARY KEY,
        source_record_id INTEGER NOT NULL REFERENCES legal_source_records(source_record_id) ON DELETE CASCADE,
        target_type TEXT NOT NULL,
        target_id INTEGER,
        target_label TEXT NOT NULL DEFAULT '',
        citation_kind TEXT NOT NULL DEFAULT 'Supports',
        pinpoint TEXT NOT NULL DEFAULT '',
        proposition TEXT NOT NULL DEFAULT '',
        excerpt TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_legal_citation_target ON legal_citation_links(target_type,target_id);
    CREATE INDEX IF NOT EXISTS idx_legal_citation_source ON legal_citation_links(source_record_id);
    """)

def _migration_13(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS legal_research_bundles (
        bundle_id INTEGER PRIMARY KEY,
        case_id INTEGER REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        research_question TEXT NOT NULL DEFAULT '',
        scope_notes TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Working',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_research_bundles_case ON legal_research_bundles(case_id);
    CREATE TABLE IF NOT EXISTS legal_research_issues (
        research_issue_id INTEGER PRIMARY KEY,
        bundle_id INTEGER NOT NULL REFERENCES legal_research_bundles(bundle_id) ON DELETE CASCADE,
        issue_title TEXT NOT NULL,
        material_facts TEXT NOT NULL DEFAULT '',
        legal_question TEXT NOT NULL DEFAULT '',
        provisional_view TEXT NOT NULL DEFAULT '',
        issue_status TEXT NOT NULL DEFAULT 'Open',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_research_issues_bundle ON legal_research_issues(bundle_id);
    CREATE TABLE IF NOT EXISTS legal_research_arguments (
        argument_id INTEGER PRIMARY KEY,
        research_issue_id INTEGER NOT NULL REFERENCES legal_research_issues(research_issue_id) ON DELETE CASCADE,
        argument_type TEXT NOT NULL DEFAULT 'Proposed',
        argument_text TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Draft',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS legal_research_issue_sources (
        issue_source_id INTEGER PRIMARY KEY,
        research_issue_id INTEGER NOT NULL REFERENCES legal_research_issues(research_issue_id) ON DELETE CASCADE,
        source_record_id INTEGER NOT NULL REFERENCES legal_source_records(source_record_id) ON DELETE CASCADE,
        position TEXT NOT NULL DEFAULT 'Relevant',
        pinpoint TEXT NOT NULL DEFAULT '',
        relevance_note TEXT NOT NULL DEFAULT '',
        proposition TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(research_issue_id,source_record_id,pinpoint)
    );
    CREATE INDEX IF NOT EXISTS idx_research_issue_sources ON legal_research_issue_sources(research_issue_id);
    """)

def _migration_14(conn):
    columns={r["name"] for r in conn.execute("PRAGMA table_info(revenue_case_drafts)")}
    if "research_bundle_id" not in columns:
        conn.execute("ALTER TABLE revenue_case_drafts ADD COLUMN research_bundle_id INTEGER REFERENCES legal_research_bundles(bundle_id) ON DELETE SET NULL")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_case_draft_sources (
        draft_source_id INTEGER PRIMARY KEY,
        draft_id INTEGER NOT NULL REFERENCES revenue_case_drafts(draft_id) ON DELETE CASCADE,
        source_record_id INTEGER REFERENCES legal_source_records(source_record_id) ON DELETE SET NULL,
        source_title_snapshot TEXT NOT NULL,
        source_type_snapshot TEXT NOT NULL DEFAULT '',
        source_identifier_snapshot TEXT NOT NULL DEFAULT '',
        source_url_snapshot TEXT NOT NULL DEFAULT '',
        position TEXT NOT NULL DEFAULT 'Relevant',
        pinpoint TEXT NOT NULL DEFAULT '',
        proposition TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        legal_status_snapshot TEXT NOT NULL DEFAULT 'unverified',
        officiality_snapshot TEXT NOT NULL DEFAULT 'unknown',
        UNIQUE(draft_id,source_record_id,pinpoint,position)
    );
    CREATE INDEX IF NOT EXISTS idx_case_draft_sources_draft ON revenue_case_draft_sources(draft_id);
    """)

def _migration_15(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_document_metadata (
        document_id INTEGER PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
        record_date TEXT,
        issuing_authority TEXT NOT NULL DEFAULT '',
        record_reference TEXT NOT NULL DEFAULT '',
        village TEXT NOT NULL DEFAULT '',
        tehsil TEXT NOT NULL DEFAULT '',
        district TEXT NOT NULL DEFAULT '',
        khasra_numbers TEXT NOT NULL DEFAULT '',
        khata_number TEXT NOT NULL DEFAULT '',
        jamabandi_year TEXT NOT NULL DEFAULT '',
        metadata_status TEXT NOT NULL DEFAULT 'unverified',
        page_notes TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS revenue_case_document_links (
        link_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        document_id INTEGER NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
        party_id INTEGER REFERENCES revenue_case_parties(party_id) ON DELETE SET NULL,
        issue_id INTEGER REFERENCES revenue_case_issues(issue_id) ON DELETE SET NULL,
        link_type TEXT NOT NULL DEFAULT 'Evidence',
        page_reference TEXT NOT NULL DEFAULT '',
        relevance_note TEXT NOT NULL DEFAULT '',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(case_id,document_id,party_id,issue_id,link_type,page_reference)
    );
    CREATE INDEX IF NOT EXISTS idx_case_document_links_case ON revenue_case_document_links(case_id);
    CREATE INDEX IF NOT EXISTS idx_case_document_links_document ON revenue_case_document_links(document_id);
    CREATE VIRTUAL TABLE IF NOT EXISTS document_text_fts USING fts5(
        document_title, original_filename, document_type, extracted_text,
        tokenize='unicode61'
    );
    INSERT INTO document_text_fts(rowid,document_title,original_filename,document_type,extracted_text)
    SELECT document_id,COALESCE(document_title,''),COALESCE(original_filename,''),
      COALESCE(document_type,''),COALESCE(extracted_text,'') FROM documents;
    CREATE TRIGGER IF NOT EXISTS document_text_ai AFTER INSERT ON documents BEGIN
      INSERT INTO document_text_fts(rowid,document_title,original_filename,document_type,extracted_text)
      VALUES(new.document_id,COALESCE(new.document_title,''),COALESCE(new.original_filename,''),
        COALESCE(new.document_type,''),COALESCE(new.extracted_text,''));
    END;
    CREATE TRIGGER IF NOT EXISTS document_text_ad AFTER DELETE ON documents BEGIN
      DELETE FROM document_text_fts WHERE rowid=old.document_id;
    END;
    CREATE TRIGGER IF NOT EXISTS document_text_au AFTER UPDATE ON documents BEGIN
      DELETE FROM document_text_fts WHERE rowid=old.document_id;
      INSERT INTO document_text_fts(rowid,document_title,original_filename,document_type,extracted_text)
      VALUES(new.document_id,COALESCE(new.document_title,''),COALESCE(new.original_filename,''),
        COALESCE(new.document_type,''),COALESCE(new.extracted_text,''));
    END;
    """)

def _migration_16(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS revenue_ownership_review_items (
        review_item_id INTEGER PRIMARY KEY,
        case_id INTEGER NOT NULL REFERENCES revenue_cases(case_id) ON DELETE CASCADE,
        village TEXT NOT NULL DEFAULT '',
        khasra_number TEXT NOT NULL DEFAULT '',
        owner_name TEXT NOT NULL DEFAULT '',
        review_type TEXT NOT NULL DEFAULT 'Discrepancy',
        observation TEXT NOT NULL,
        question_for_review TEXT NOT NULL DEFAULT '',
        source_document_id INTEGER REFERENCES documents(document_id) ON DELETE SET NULL,
        page_reference TEXT NOT NULL DEFAULT '',
        review_status TEXT NOT NULL DEFAULT 'Open',
        verification_status TEXT NOT NULL DEFAULT 'unverified',
        resolution_note TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_ownership_review_case ON revenue_ownership_review_items(case_id,review_status);
    CREATE INDEX IF NOT EXISTS idx_ownership_review_khasra ON revenue_ownership_review_items(village,khasra_number);
    """)
