# Changelog

## V0.1.0-A3
- Added schema migration v3 and judgment research FTS5 index.
- Added party, court and subject metadata to judgments.
- Added advanced judgment search and filters.
- Added judgment detail reader and official-source link.
- Added subject topics, statutory references and related-judgment relationships.
- Restored create_backup/restore_backup compatibility helpers for the A2 regression test.
- Added judgment research and backup compatibility tests.


## V0.1 A4 — Official Online Source Importer
- Added a user-initiated HTTPS importer for PDF and plain-text files from a restricted allowlist of official publisher hosts.
- Added redirect-host validation, 40 MB size limit, content-type checks, exact SHA-256 duplicate detection and import provenance.
- Added Online Sources history page and schema migration V4.
- No scraping, background polling, automatic replacement, or automatic legal-status verification.


## V0.1 A5 — Haryana Revenue Law Library
- Added schema V5 and a curated revenue-law material register with search, filters, provenance fields and explicit legal-review states.
- Seeded initial records for the Punjab Land Revenue Act, 1887 as applicable to Haryana; Haryana Land Revenue (Amendment) Act, 2025; Haryana Land Records Manual Gazette amendment (2021); and Haryana Abadi Deh Act, 2025 / Haryana Act No. 4 of 2026.
- Added manual entry and source-opening workflow.
- Seed entries distinguish official portals, government-hosted Gazette copies and secondary copies; no item is represented as fully consolidated/current law.


## V0.1 A6 — Haryana Revenue Research Workspace
- Added schema V6: provision/section records with effective periods and source references; annotations; amendment history; legal-material relationships; research topics and material-topic links.
- Added Section Reader with saved-text preview and manual add/edit; annotations and research notes; amendment timeline; cross-reference links; seeded topic workspaces.
- All section text and legal relationships are user-entered and carry explicit verification states. No statutory wording is automatically inferred or certified.


## V0.1 A7 — Revenue Case Management
- Added schema V7 for revenue cases, parties, land/property particulars, chronology/hearings, evidence links and legal issues/arguments.
- Replaced the My Cases placeholder with a working My Revenue Cases page: create, edit, search, status-filter and delete cases.
- Added case-specific tabs to record parties, khasra/khata/Jamabandi particulars, events and hearing actions, evidence linked to existing Document Library items, and legal issues with proposed arguments and relevant law.
- Deleting a case cascades its case records but does not delete source documents from the general Document Library.
- Added tests for migration, CRUD, filtering, linked records and cascade deletion.


## V0.1 A8 — Revenue Case Document & Drafting Studio
- Added schema V8 for case drafts, evidence-to-party/issue relationships and report export history.
- Added Case Drafting Studio with per-case draft creation, editing, status management, version counter, deletion and TXT export.
- Added evidence connections to relevant parties and legal issues.
- Added consolidated case-preparation TXT report covering case details, parties, property, chronology, evidence, issues, connections, draft register and private preparation notes.
- Preserved original Document Library records; case evidence continues to reference existing documents rather than duplicate them.
- Added migration, draft lifecycle, evidence connection, report and cascade tests.


## V0.1 A9 — Revenue Records Intelligence
- Added schema V9 for source-based revenue record snapshots, owner/khasra entries and mutation history.
- Added Revenue Records Intelligence page to register Jamabandi, Mutation, Girdawari and other record snapshots, optionally linking them to cases and existing source documents.
- Added owner-wise Khewat, Khata, Khatauni, Khasra, area, unit and share recording.
- Added same-village snapshot comparison by Khasra number and owner name, with added/missing/changed/no-difference review results.
- Added mutation history register and status/source references.
- Added area conversions and fractional-share calculations, plus integrity flags for entered shares exceeding 1 and inconsistent repeated area values.
- Added tests for migration, record CRUD, mutation history, comparisons, area arithmetic, integrity checks and cascade deletion.


## V0.1 A10 — Haryana Partition & Ownership Analysis
- Added schema V10 for partition working plans and Khasra-wise proposed allocations.
- Added ownership analysis from a selected source record set, including owner-wise calculated entitlement area, Khasra share totals and arithmetic review flags.
- Added partition worksheet management linked to a case and source record set, with proposed area/share allocations per co-sharer and Khasra.
- Added reconciliation of proposed allocated area against the entered source parcel area, proposed share-total checks and duplicate allocation warnings.
- Added exportable partition working statement with assumptions, recorded analysis, proposed allocations, reconciliation and limitations.
- Added tests for schema, ownership arithmetic, shortfalls, plan CRUD, allocation reconciliation, report output and cascade deletion.





## V0.1 A11 — Revenue Case Strategy & Procedure Assistant
- Corrected the schema version constant to V10 baseline and added V11 migration for proceeding workflows, preparation steps and proceeding events/deadlines.
- Added case-linked workflows for mutation, partition, appeal, revision, record correction, Abadi Deh and other proceedings.
- Added generic, idempotent checklist prompts for common proceeding types; every prompt is explicitly marked unverified and requires source checking.
- Added user-entered limitation review fields for triggering event, legal period note, source reference, reviewer, review date, manually verified due date and caveats. No limitation calculation is performed.
- Added step status, target/completion dates, responsibility and legal source verification; added proceeding chronology and deadline register.
- Added exportable procedure working sheet and tests for migration, workflow CRUD, checklist/event lifecycle, templates and warnings.


## V0.1 A12 — Legal Source Verification & Citation Engine
- Added schema V12 source provenance register, source version/effective-date history and reusable citation links.
- Added source identity, publisher, jurisdiction, URL, Gazette/Act/case identifier, publication/retrieval/effective dates, officiality classification, legal-status review, verification state, reviewer and notes.
- Added SHA-256 snapshot preservation: selected source files are copied into the app's local documents/legal_sources directory using their content hash as the filename; hash identity is not authenticity certification.
- Added amendment/version history and citation links with pinpoint references, proposition, relationship, short excerpt and verification state.
- Added legal source dossier export and status summary counts.
- Added validation and regression tests for schema, source lifecycle, date validation, snapshot preservation, version history, citation links and cascading deletion.
- No automatic web crawling, authenticity certification, commencement determination, legal status conclusion or precedential-status determination.


## V0.1 A13 — Haryana Legal Research Intelligence & Case Argument Builder
- Added schema V13 case-linked legal research bundles, issue registers, structured arguments and issue-to-source links.
- Added combined local search across registered legal sources and their linked Act/material metadata, section text, judgment titles, citations, keywords and judgment text. Search explicitly covers only registered source records.
- Added bundle and issue CRUD, source attachment with supporting/contrary/relevant classifications, pinpoint references, propositions, relevance notes and verification state.
- Added structured argument types and review states, including proposed arguments, responses to contrary authority and counter-arguments.
- Added consolidated export with source verification, legal status, officiality, reviewer, URL and hash provenance, plus explicit safeguards against treating search coverage or labels as legal conclusions.
- Added migration, search, cascade, duplicate attachment, source linking and report tests.


## V0.1 A14 — Legal Drafting & Submission Preparation Studio
- Added schema V14 link from revenue case drafts to research bundles and durable draft-source citation snapshots.
- Added Research-to-Draft tab to the existing Case Drafting Studio.
- Added case-aware selection of research bundles, including general bundles and bundles linked to the selected case only.
- Added a structured editable draft scaffold assembled from issue facts, legal questions, provisional views, proposed arguments and supporting/contrary source pinpoints.
- Added a source and pinpoint schedule to draft export, preserving source title/type/identifier/URL, position, pinpoint, proposition, verification state, legal-status review and officiality classification.
- Draft source snapshots survive deletion of a source-register entry; source links cascade when a draft is deleted.
- Added tests for migration, case scoping, assembly, citation snapshots, exports and deletion behavior.
- Does not generate legal advice, decide legal issues, populate prescribed forms or certify filing readiness.


## V0.1 A15 — Haryana Revenue Case Intelligence Dashboard
- Added a consolidated, read-only operational dashboard for revenue case management.
- Added per-case rollups for parties, evidence, evidence verification review, open case/research issues, working drafts, active proceedings, outstanding checklist steps and past recorded deadlines.
- Added upcoming case hearing register.
- Added recorded proceeding deadline register, distinguishing past recorded dates from future dates without asserting legal expiry.
- Added outstanding proceeding preparation steps with target dates, responsibility and source/verification references.
- Added a limitation review register displaying manually entered start date, period note, source reference, reviewer, review date, entered due date and caveat.
- Limitation dates are not calculated or legally validated by the dashboard.
- Added five dashboard service tests; full suite now passes 76 tests.


## V0.1 A16 — Legal Document Intelligence & Evidence Analysis
- Added schema V15 with a document metadata register for revenue record dates, issuing offices, record references, village/tehsil/district, Khasra, Khata and Jamabandi year.
- Added FTS5 index over document titles, filenames, types and extracted text, including insert/update/delete synchronization triggers.
- Added document search with text snippets and metadata fallback search.
- Added case-document relationships with optional party and issue links, document role, page/paragraph reference, relevance note and verification state.
- Added case evidence index export with document and linkage details.
- Case-document links are separate from the original Document Library; unlinking does not delete the source file.
- Added tests for search indexing, metadata, case scoping, duplicate handling, link deletion and provenance-preserving evidence index.
- OCR, handwriting recognition, authenticity, admissibility and legal conclusions are not provided.


## V0.1 A17 — Land Record Comparison & Ownership Evidence Workspace
- Added schema V16 ownership discrepancy/review register linked to cases and optional source documents.
- Added cross-year ownership history by village and optional Khasra, showing each registered record snapshot and owner entry.
- Added normalized Khasra/owner comparisons across two record sets, identifying added, absent, changed and duplicate matching rows.
- Added mutation chronology view with Khasra token filtering and linked case/village context.
- Added source trace linking record-set snapshots to their source document and existing case-document page references.
- Added case-level discrepancy/review CRUD with status, verification, page reference, question and resolution note.
- Added consolidated ownership history and evidence report export.
- Comparisons use normalized owner names and entered fields only; they do not resolve identity, title, succession, mutation validity or legal entitlement.
- Added nine A17 tests; full suite target is reported below after validation.
