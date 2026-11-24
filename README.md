# JASS Legal & Revenue Desk — V0.1 A3

A3 adds the local Judgment Research Engine.

## New features
- Search judgment title, case number, citation, court, parties, judge, subject keywords and full text.
- Filter by court, decision year, subject topic and verification status.
- Judgment detail reader.
- Add manually verified subject topics.
- Record statutory references with section and context.
- Link related judgments with a relationship type and researcher notes.
- Open an official source URL in the system browser.
- Schema migration v3 with judgment research FTS5 index.

## Scope and legal-data limitations
Search operates on locally imported or manually entered judgment records only. A3 does not automatically crawl court websites or guarantee comprehensive coverage. A citation, statutory reference or judicial treatment entered by a user remains unverified until independently checked against an authoritative source. The application never automatically labels a judgment as followed, distinguished, overruled or binding.

## Installation
Python 3.10+:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
Windows PowerShell:
```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Tests
```bash
python -m unittest discover -s tests -v
```

## Upgrade notes
A3 migrates existing A1/A2 databases to schema version 3. Back up the database before upgrading. Existing records are retained; new judgment metadata fields default to blank.


## A4 — Official online source imports
The **Official Online Sources** page accepts direct HTTPS PDF or plain-text document URLs from these allowlisted hosts: `indiacode.nic.in`, `sci.gov.in`, `highcourtchd.gov.in`, and `egazette.gov.in`. The importer is explicitly user-initiated, validates redirects, limits downloads to 40 MB, rejects unsupported content, detects exact duplicates by SHA-256, and records requested/final URL and import metadata. It does not crawl websites or silently replace prior files. A scheduled update checker / remote-change monitor is not included in this A4 build; imported files remain immutable snapshots in the local library. HTML landing pages are not imported; open the official page and copy the direct PDF link.

**Important:** an allowlisted official host is not a legal-status opinion. Check the document's authenticity, completeness, amendments, commencement, repeal and current applicability independently. Haryana-specific Gazette sources are not yet included in the allowlist pending endpoint validation.


## A5 — Haryana Revenue Law Library
A5 adds a curated **Haryana Revenue Law Library** register. Initial entries cover the Punjab Land Revenue Act, 1887 as applicable to Haryana; the Haryana Land Revenue (Amendment) Act, 2025; a 2021 Haryana Land Records Manual Gazette amendment; and the Haryana Abadi Deh legislation published in 2026. Each record stores jurisdiction, type, year, Act/notification number, publication/effective dates, subjects, description, source URL, source classification, legal-review state and verification notes. Users can search/filter, add material, inspect notes and open source links.

The initial register is a research index, not a consolidated bare-act database or legal opinion. In particular, the 1887 Act requires Haryana-specific consolidation and amendment review; the 2025 section 111A change also refers to commencement notifications for individual revenue estates. The source classifications and verification notes identify where an official issue or later amendment still needs checking.


## A6 — Haryana Revenue Research Workspace
A6 adds the **Haryana Revenue Research Workspace** with five tabs: (1) Section Reader for user-entered provision text, source references and effective periods; (2) Annotations & Notes linked to a material and optionally a section; (3) Amendment Timeline with affected section, amending instrument, dates, summary and verification status; (4) Legal Connections linking related Acts, rules, notifications and other library entries; and (5) Research Topics. Initial topics include Mutation, Jamabandi / Record of Rights, Inheritance / Succession, Partition, Girdawari, Revenue Courts and Appeals, Abadi Deh, and Land Records Administration.

The app intentionally does not ship invented or unverified bare-act wording. Populate section text from an authenticated source, record its exact page / paragraph and set the verification state appropriately. An effective date left blank means unknown, not necessarily currently in force.


## A7 — Revenue Case Management
A7 replaces the My Cases placeholder with **My Revenue Cases**. Create, edit, search and filter cases by status. Each case has tabs for parties and representatives; land/property particulars (village, tehsil, district, hadbast, Jamabandi year, khata, khatauni, khasra numbers, area and share); chronology and hearings; evidence items optionally linked to existing Document Library documents; and legal issues with facts, legal questions, proposed arguments and relevant law references.

Case records are stored in the local SQLite database. The app currently does not encrypt the database or implement user authentication; protect the operating-system account, device and backups accordingly. Do not store passwords, banking credentials or unnecessary identity numbers. The date fields are record-keeping fields only: the app does not calculate statutory limitation or guarantee hearing reminders. Deleting a case removes its case-specific records but preserves documents in the general Document Library.


## A8 — Revenue Case Document & Drafting Studio
A8 adds a **Case Drafting Studio** for each case. It supports working drafts for applications, appeals, revisions, objections, replies, written submissions and evidence lists. Drafts can be edited, assigned a status, exported as UTF-8 text and version-counted when updated. It also connects evidence register items to one or both of a case's parties and legal issues.

The Case Reports tab exports a consolidated UTF-8 `.txt` case-preparation report with the case register, parties, property particulars, chronology, evidence, evidence connections, issues and draft register. It intentionally does not insert legal wording or generate a legally validated pleading. Drafts and reports are preparation aids: verify applicable law, court/revenue forum requirements, limitation, facts, annexures, signatures and filing rules before use.


## A9 — Revenue Records Intelligence
A9 adds **Revenue Records Intelligence**. Register source snapshots (Jamabandi, Mutation, Girdawari, Fard/record extract or Other) by village and year/period, link them optionally to a case and an existing Document Library item, and record source reference and verification status. Add owner-wise entries with Khewat, Khata, Khatauni, Khasra, owner/parent name, area/unit and share fraction.

The Mutation History tab records mutation number/date/type, predecessor and successor, Khasra references, area/share, status and source. The Year Comparison tab compares two record sets from the same village using case-insensitive Khasra + owner matching. The calculator converts acre, kanal, marla, square yards, hectare and square metres and calculates fractional shares. Integrity checks flag entered share totals above one and differing area values within a Khasra group.

Comparisons are screening aids, not authoritative reconciliation: spelling variations, duplicate entries, different area bases, record corrections and source page context can affect results. A missing match is not proof that ownership ended; a changed entry is not proof of an unlawful mutation. The app does not determine title, possession, inheritance entitlement or legal validity. Always inspect original certified records and orders. Area conversion uses 1 acre = 8 kanal = 160 marla = 4,840 square yards.


## A10 — Haryana Partition & Ownership Analysis
A10 adds **Partition & Ownership Analysis**. Select a revenue record set to review Khasra-wise recorded owners, row counts, entered parcel area, recorded share totals and owner-wise calculated entitlement area. The analysis flags incomplete shares, totals above/below 100%, repeated owner entries and ambiguous or differing area values.

Create a partition working plan linked to a source record set and optionally to a case. Add proposed allocations by Khasra and co-sharer, including proposed area/unit, optional share fraction and location/quality/access/irrigation notes. The worksheet compares proposed area totals against the entered source parcel area and checks proposed share totals. Export a UTF-8 text partition working statement.

**Interpretation limits:** recorded shares and area entries are only as reliable as the source material and data entry. Owner-wise calculated entitlement is a mathematical calculation from entered parcel area × entered share, not a determination of title. The same full parcel area may be repeated on multiple owner rows; the tool treats this as a parcel area basis only when all values agree. A proposed physical allocation is not a partition order and does not account automatically for shape, frontage, access, soil, irrigation, encumbrances, possession, valuation, minimum parcel rules or applicable statutory procedure. Review with certified records and the competent authority before relying on a proposal.





## A11 — Revenue Case Strategy & Procedure Assistant
A11 adds a **Procedure Assistant** linked to My Revenue Cases. Track separate mutation, partition, appeal, revision, correction, Abadi Deh or other proceeding workflows. Record forum, case reference, stage, status, preparation checklist, responsible person, target/completion dates, source references and verification state. Record events, hearings, orders, next actions and manually entered deadline dates.

The limitation review area records a potential starting event/date, manually researched period, legal source, reviewer, review date, user-entered due date and caveats. The software deliberately does not calculate limitation or decide the correct forum, maintainability, exclusions, condonation or mandatory procedure. Generic checklist prompts are not legal requirements and are marked unverified. Each step should be checked against the current consolidated statute, amendments, rules, notifications, relevant orders and local filing practice.

Export a UTF-8 text procedure working sheet for the case file. The report carries the same limitation and legal-verification cautions.


## A12 — Legal Source Verification & Citation Engine
A12 adds the **Legal Source Verification** workspace. Maintain source records for Acts, amendments, rules, Gazette notifications, circulars, manuals, judgments and other material. Capture publisher, jurisdiction, exact URL, Gazette/Act/case identifier, publication and retrieval dates, effective period, officiality classification, legal-status review, verification state, reviewer and notes. Existing revenue-library materials, sections, judgments and documents can be linked by their local record IDs.

### Preserve and identify source copies
Use **Preserve & hash snapshot** to copy a selected source file into the application's local `documents/legal_sources` folder. The SHA-256 digest is stored with the source record; identical bytes use the same hash-based filename. This preserves a local copy and supports later byte-level comparison. A hash does not prove that a document is genuine or was published by the authority named.

### Version history and citations
Record each amendment/version with its instrument reference, publication date, effective period, source reference, change summary and verification state. Link a source to a revenue case, proceeding, draft, preparation step, research topic or another target. Record the pinpoint (section, paragraph or page), proposition, relationship (supports, contradicts, amends, interprets, etc.), optional short excerpt and verification state. Export a source dossier with its provenance, version history and citation links.

### Important limits
The application does not crawl the web or automatically determine authenticity, commencement, current force, territorial application, repeal/savings effect or binding precedential status. Official-host classification and legal-status fields are human-entered review records, not automatic conclusions. Check original official publications, exact Gazette issues, commencement notifications, subsequent amendments, repeal/savings clauses and later judicial treatment before relying on a proposition.


## A13 — Haryana Legal Research Intelligence & Case Argument Builder
A13 adds a research workspace that organizes locally registered legal sources by case and legal issue. Create a general research bundle or link it to a revenue case, state the research question and scope, and create issue records with material facts, legal questions and a provisional view.

### Search registered authorities
Search source records registered in A12. The search checks source title, identifier, publisher and notes, plus linked revenue material titles, section numbers/headings/text, judgment titles/citations/keywords and judgment full text. Filter by jurisdiction and source verification state. Only registered source records appear. This is not a comprehensive legal database or live case-law search; no result does not mean no authority exists.

### Build issue-wise argument sheets
Attach source records to an issue as **Supports**, **Contrary**, **Relevant**, **Distinguishes** or **Procedural**. Record a pinpoint section/paragraph/page, proposition, relevance/treatment note and verification state. Add proposed arguments, counter-arguments, responses to contrary authority, relief sought and research notes with review states. Supporting/contrary labels are researcher classifications, not court determinations.

### Export
Export a consolidated TXT bundle containing the research question, scope, issues, facts, legal questions, provisional views, arguments, source pinpoints, propositions, source verification and provenance. The export includes safeguards reminding the researcher to check effective dates, amendments, repeal/savings provisions, court hierarchy, later treatment and procedural posture.

A13 does not generate legal conclusions or draft court-ready submissions automatically. It provides a structured, source-linked research workspace; verify all material against primary sources and seek qualified legal review before relying on it.


## A14 — Legal Drafting & Submission Preparation Studio
A14 connects the A13 issue-led research workspace to the existing Case Drafting Studio.

### Create a draft from research
Open **Case Drafting Studio → Research-to-Draft** and select a revenue case. The bundle selector shows research bundles linked to that case and general research bundles; bundles linked to another case are excluded. Select a bundle, choose a document type and title, preview the scaffold and create the draft.

The generated scaffold organizes each research issue into material facts, legal question, proposed submissions, provisional view and source references. It includes supporting and contrary authorities with their pinpoint references, propositions and verification information. It also provides spaces for relief/prayer and verification/annexures. All content is editable in the existing Drafting Workspace.

### Citation schedule and provenance
The created draft retains separate snapshots of source title, type, identifier, URL, support/contrary classification, pinpoint, proposition, verification status, legal-status review and officiality classification. Export using **Export selected draft with source schedule** to include both the editable draft text and a consolidated source schedule. Snapshot details remain with the draft if a source-register entry is later deleted.

### Important limits
This feature assembles a research scaffold, not a prescribed court form, legal opinion or filing-ready submission. It does not invent missing facts, select the correct forum, calculate limitation, determine legal applicability or decide which arguments should be advanced. Verify all source text, pinpoint citations, adverse authorities, effective dates, procedure, prescribed forms, service, fees and filing requirements against current authoritative materials. Obtain qualified legal review where appropriate.


## A15 — Haryana Revenue Case Intelligence Dashboard
A15 adds a consolidated read-only dashboard to the sidebar as **Revenue Case Intelligence Dashboard**.

### Case Overview
The case table rolls up case status, next hearing date, parties, evidence, evidence needing verification review, open case issues, open research issues, working drafts, active proceedings, outstanding procedural steps and past recorded proceeding deadlines.

### Upcoming Hearings
Shows future hearing dates entered in the case register. It does not infer hearings from unstructured notes.

### Recorded Deadlines
Shows dates manually entered against proceeding events. Past recorded dates are surfaced for review; the dashboard does not decide whether a legal deadline has expired or whether an extension, exclusion or other rule applies.

### Outstanding Preparation
Lists incomplete proceeding checklist items with target date, responsible person, source reference and verification status.

### Limitation Review Register
Displays the limitation review fields entered in Procedure Assistant, including the start date, researched period note, source reference, reviewer, review date, entered due date and caveat. It does not calculate limitation, determine the correct trigger date or validate the entered period. A past entered date is a prompt to verify, not a legal conclusion.

### Operating note
The dashboard is a roll-up of information already stored in the local database. Missing information is not evidence that no hearing, deadline, issue or obligation exists. Keep case records current and verify all procedural dates and legal requirements against authoritative sources.


## A16 — Legal Document Intelligence & Evidence Analysis
A16 adds **Legal Document Intelligence** to the sidebar and builds on the existing Document Library. Import PDFs and TXT files through **Documents** first; A16 works with those registered library items and does not independently duplicate or move them.

### Document Search
Search across extracted text, document title, filename, document type and selected revenue metadata such as record reference, village and Khasra numbers. Search results show extraction status and a text-match excerpt. Select a result and open **Extracted Text** to inspect the text stored by the import process.

The search index is local SQLite FTS5 and is synchronised when a document is inserted, updated or deleted. Documents with no text layer, scanned image-only pages or unsupported formats may have no searchable text.

### Revenue Metadata
Select a document and choose **Edit metadata** to record the record date, issuing authority, record number/reference, village, tehsil, district, Khasra numbers, Khata/Khatauni, Jamabandi year and verification status. These are researcher-entered fields; the app does not certify them from the source.

### Case Evidence Links
Select a case and choose **Link to case**. Link an existing library document to the case, optionally associating it with a party and/or legal issue. Record the document's role, pinpoint page/paragraph, relevance, verification status and notes. The same library document can be linked to multiple cases. Removing a link does not delete the document or its stored original.

### Evidence Index Export
Export a case-specific text index showing linked documents, parties, issues, page references, revenue metadata and verification notes. This is a preparation aid, not an evidentiary ruling or certificate.

### Extraction and legal limits
PDF text extraction uses the existing optional PyMuPDF dependency. A PDF without a text layer may report `no_text_layer`; A16 does not perform OCR, handwriting recognition, image interpretation or automatic transcription. Check scanned pages visually and preserve the original. Extracted text may omit tables, seals, marginal notes, handwriting, maps, stamps or layout context. File hashes support byte-level duplicate identification only; they do not prove authenticity, completeness, admissibility, ownership or legal effect.


## A17 — Land Record Comparison & Ownership Evidence Workspace
A17 adds **Ownership Evidence Workspace** to the sidebar. It connects the A9 Revenue Records register, A16 Document Library evidence links and existing mutation register.

### Ownership History
Choose an optional case, village and optional exact Khasra number. The table displays every matching registered ownership entry across record sets and years, including owner/parent name, Khewat, Khata, Khatauni, area, share fraction, record-set verification state and source document reference. Each row is a transcription in a particular local snapshot; it is not an independently verified title history.

### Year Comparison
Choose two different record snapshots belonging to the selected village. The comparison groups entries by normalized Khasra and owner name, then reports owners added in the later snapshot, owners absent from it, changed recorded fields and duplicate matching rows. Name matching only normalizes case and whitespace. It cannot reliably reconcile spelling differences, aliases, changed names, inheritance, joint interests or partition events. Review the source entries and original documents before drawing conclusions.

### Mutation History
Shows registered mutation records associated with the selected village/case, with date, mutation number/type, Khasra references, parties, area, status and source reference. Khasra filtering tokenizes comma/semicolon-separated references. A mutation entry is not proof that the mutation was legally valid, correctly entered or implemented.

### Source Trace
Connects each registered record set to its source document and any existing case-document link, including page reference and verification state. Missing links indicate missing local linkage, not necessarily absence of a source document in the real world.

### Discrepancy Register
For a selected case, record ownership claims, discrepancies, missing records, name variations, share/area issues or mutation-tracing questions. Record the observation, question, source page, review status, verification state and resolution note. This is a research checklist, not an adjudication of competing claims.

### Export
Export an ownership history and evidence report for the selected village, optional case and Khasra. The report contains the registered snapshots, mutation chronology, source trace and important limitations.

### Data and legal safeguards
A17 does not infer title, determine whether an owner was lawfully added/removed, validate succession, establish mutation validity, calculate legal shares, or decide possession. It cannot establish that the local record set is complete. Verify all entries against original/certified Jamabandi, mutation orders, relevant revenue proceedings and other primary material. Preserve contrary records and explain discrepancies rather than silently reconciling them.
