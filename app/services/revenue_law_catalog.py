"""Seed and query the curated Haryana revenue-law research register."""
SEED_MATERIALS = [
    {
        "title": "Haryana Government e-Gazette Portal",
        "material_type": "Official Source Portal",
        "jurisdiction": "Haryana",
        "year": None,
        "act_number": "",
        "publication_date": None,
        "subject_tags": "official gazette;acts;notifications;orders;legislative supplement",
        "description": "Official Haryana Government Gazette portal. The Government describes the Gazette as the authorised public journal for notifications and orders. Use this portal to locate the original issue and preserve the exact Gazette part, date and page references.",
        "source_name": "Government of Haryana",
        "source_url": "https://www.haryana.gov.in/e-gazette/",
        "source_classification": "official_government_portal",
        "legal_status": "source_directory_only",
        "verification_notes": "Portal landing page only; retrieve and retain the individual Gazette issue for each legal proposition."
    },
    {
        "title": "Haryana Government Digital Repository",
        "material_type": "Official Source Portal",
        "jurisdiction": "Haryana",
        "year": None,
        "act_number": "",
        "publication_date": None,
        "subject_tags": "acts;notifications;legal documents;public access;revenue department",
        "description": "Government of Haryana Digital Repository. Its public-access entry states that guests can search and browse legal documents, Acts and notifications without logging in.",
        "source_name": "Government of Haryana",
        "source_url": "https://hgdr.csharyana.gov.in/",
        "source_classification": "official_government_repository",
        "legal_status": "source_directory_only",
        "verification_notes": "Search result portal; verify each record's issuing department, document identity, Gazette publication and current legal status."
    },
    {
        "title": "Punjab Land Revenue Act, 1887 (as applicable to Haryana)",
        "material_type": "Principal Act",
        "jurisdiction": "Haryana",
        "year": 1887,
        "act_number": "Punjab Act No. 17 of 1887",
        "publication_date": "1887-09-23",
        "subject_tags": "record of rights;jamabandi;mutation;partition;revenue officers;appeals;assessment",
        "description": "Principal land-revenue statute applied in Haryana with state adaptations and amendments. The original enactment must not be treated as a current consolidated Haryana text. Confirm the Haryana-adapted text, omitted provisions, amendments, commencement notifications and rules before relying on any section.",
        "source_name": "PRS Legislative Research (secondary text) / Haryana e-Gazette portal",
        "source_url": "https://prsindia.org/files/bills_acts/acts_states/haryana/1887/1887HR17.pdf",
        "source_classification": "secondary_copy_official_text_to_be_located",
        "legal_status": "consolidation_and_amendments_to_verify",
        "verification_notes": "A searchable copy is available from PRS, but it is not the official publisher. Haryana adaptation is described in the text. Confirm current consolidated text and all amendments against Haryana Gazette / Government repository. Section 48–60 has been omitted in Haryana by Haryana Act No. 24 of 1986 according to secondary case-law text; independently verify exact amending instrument and effect."
    },
    {
        "title": "Haryana Land Revenue (Amendment) Act, 2025",
        "material_type": "Amending Act",
        "jurisdiction": "Haryana",
        "year": 2025,
        "act_number": "Haryana Act No. 14 of 2025",
        "publication_date": "2025-04-16",
        "effective_date": "2025-04-16",
        "subject_tags": "partition;joint holding;co-sharers;section 111A;section 114",
        "description": "The published amendment changes the marginal heading and sub-section (1) of section 111A of the Punjab Land Revenue Act, 1887 as applicable to Haryana, and omits section 114. The amendment states that it comes into force on publication in the Official Gazette.",
        "source_name": "Haryana Government Gazette (official portal landing page; specific issue link to be confirmed)",
        "source_url": "https://www.haryana.gov.in/e-gazette/",
        "source_classification": "official_portal_issue_link_pending",
        "legal_status": "amendment_text_located_commencement_and_consolidation_review_required",
        "verification_notes": "Act No. 14 of 2025, assent 2025-04-08, published 2025-04-16. The amendment text was located in a Gazette reproduction; obtain and preserve the matching issue from the official Haryana Gazette portal before treating this entry as primary-source verified. Any section 111A notification applying the provision to a revenue estate must be checked separately."
    },
    {
        "title": "Haryana Land Records Manual — Chapter 7: Record of Rights (2021 amendment)",
        "material_type": "Manual / Gazette Notification",
        "jurisdiction": "Haryana",
        "year": 2021,
        "act_number": "Notification No. 573-R-2-2021/1863",
        "publication_date": "2021-04-06",
        "subject_tags": "record of rights;mutation;HARIS;HALRIS;web-HALRIS;objections;jamabandi",
        "description": "Haryana Government Gazette notification dated 16 March 2021 inserts clause (5A) in paragraph 7.1(B) of the Haryana Land Records Manual concerning automatic generation and display of certain mutations in HARIS/HALRIS/Web-HALRIS estates and the objection process described in the notification.",
        "source_name": "Haryana Government Gazette PDF hosted on Haryana government district site",
        "source_url": "https://cdnbbsr.s3waas.gov.in/s3d79c6256b9bdac53a55801a066b70da3/uploads/2023/08/202308241327044560.pdf",
        "source_classification": "government_gazette_copy_verify_issue_metadata",
        "legal_status": "historical_instruction_current_status_to_verify",
        "verification_notes": "Gazette issue shown as No. 14-2021 dated 6 April 2021; notification dated 16 March 2021. This is an amendment/instruction extract, not the entire current Land Records Manual. Check later amendments and current departmental instructions."
    },
    {
        "title": "Haryana Abadi Deh (Vesting, Recording and Resolving of Ownership Rights) Act, 2025",
        "material_type": "State Act",
        "jurisdiction": "Haryana",
        "year": 2026,
        "act_number": "Haryana Act No. 4 of 2026",
        "publication_date": "2026-01-19",
        "subject_tags": "abadi deh;ownership;record of rights;survey;mutation;svamitva",
        "description": "Haryana legislation concerning vesting, recording and resolution of ownership rights in Abadi Deh areas. The Gazette text includes provisions on records of rights and savings relating to SVAMITVA and Chapter 7A of the Haryana Land Records Manual.",
        "source_name": "Haryana Government e-Gazette portal",
        "source_url": "https://www.haryana.gov.in/e-gazette/",
        "source_classification": "official_portal_issue_link_pending",
        "legal_status": "official_issue_and_rules_to_verify",
        "verification_notes": "The issue dated 19 January 2026 is indexed in a third-party Gazette archive as Haryana Act No. 4 of 2026. Retrieve the corresponding original issue from the official Haryana e-Gazette / Haryana Government Digital Repository and check rules and commencement."
    },
]

def seed_revenue_law_catalog(conn):
    for original in SEED_MATERIALS:
        item = {"effective_date": None, **original}
        exists = conn.execute("SELECT 1 FROM revenue_law_materials WHERE title=? LIMIT 1", (item["title"],)).fetchone()
        if exists:
            continue
        conn.execute("""INSERT OR IGNORE INTO revenue_law_materials
            (title,material_type,jurisdiction,year,act_number,publication_date,effective_date,
             subject_tags,description,source_name,source_url,source_classification,legal_status,verification_notes)
            VALUES(:title,:material_type,:jurisdiction,:year,:act_number,:publication_date,:effective_date,
             :subject_tags,:description,:source_name,:source_url,:source_classification,:legal_status,:verification_notes)""", item)
    conn.commit()

def search_materials(conn, query="", material_type="All", jurisdiction="All"):
    sql = """SELECT * FROM revenue_law_materials WHERE 1=1"""
    args = []
    if query.strip():
        like = "%" + query.strip() + "%"
        sql += """ AND (title LIKE ? OR act_number LIKE ? OR subject_tags LIKE ? OR description LIKE ?
                   OR source_name LIKE ? OR verification_notes LIKE ?)"""
        args.extend([like] * 6)
    if material_type != "All":
        sql += " AND material_type=?"; args.append(material_type)
    if jurisdiction != "All":
        sql += " AND jurisdiction=?"; args.append(jurisdiction)
    sql += " ORDER BY year DESC, title COLLATE NOCASE"
    return conn.execute(sql, args).fetchall()
