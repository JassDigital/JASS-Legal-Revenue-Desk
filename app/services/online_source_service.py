"""Careful, provenance-preserving downloads from a small official-source allowlist."""
from __future__ import annotations
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError
from pathlib import Path
import hashlib, mimetypes, tempfile, os

MAX_DOWNLOAD_BYTES = 40 * 1024 * 1024
TIMEOUT_SECONDS = 25
OFFICIAL_SOURCES = {
    "India Code": {"host": "indiacode.nic.in", "publisher": "Legislative Department, Government of India", "jurisdiction": "Central", "kind": "Legislation"},
    "Supreme Court of India": {"host": "sci.gov.in", "publisher": "Supreme Court of India", "jurisdiction": "Central", "kind": "Judgment"},
    "Punjab and Haryana High Court": {"host": "highcourtchd.gov.in", "publisher": "Punjab and Haryana High Court", "jurisdiction": "Haryana/Punjab", "kind": "Judgment"},
    "eGazette of India": {"host": "egazette.gov.in", "publisher": "Government of India", "jurisdiction": "Central", "kind": "Gazette"},
}

class OnlineImportError(Exception):
    pass

class _AllowlistedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        identify_official_source(newurl)  # validate before contacting the redirect target
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def identify_official_source(url: str):
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise OnlineImportError("Only HTTPS URLs are accepted.")
    host = parsed.hostname.lower().rstrip(".")
    for name, info in OFFICIAL_SOURCES.items():
        if host == info["host"] or host.endswith("." + info["host"]):
            return name, info
    raise OnlineImportError("This host is not in the application's official-source allowlist. Add the file manually or request source review in a future update.")

class OnlineSourceService:
    def __init__(self, conn):
        self.conn = conn

    def fetch_and_import(self, url: str, title: str = "", document_type: str = "Other"):
        name, info = identify_official_source(url)
        requested = url.strip()
        request = Request(requested, headers={"User-Agent": "JASS-Legal-Revenue-Desk/0.1 (user-initiated legal research import)", "Accept": "application/pdf,text/plain"})
        try:
            response = build_opener(_AllowlistedRedirectHandler()).open(request, timeout=TIMEOUT_SECONDS)
            with response:
                final_url = response.geturl()
                final_name, final_info = identify_official_source(final_url)
                status = getattr(response, "status", 200)
                content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
                length_header = response.headers.get("Content-Length")
                if length_header and int(length_header) > MAX_DOWNLOAD_BYTES:
                    raise OnlineImportError("The remote file exceeds the 40 MB safety limit.")
                data = response.read(MAX_DOWNLOAD_BYTES + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OnlineImportError(f"Download failed: {exc}") from exc
        if len(data) > MAX_DOWNLOAD_BYTES:
            raise OnlineImportError("The remote file exceeds the 40 MB safety limit.")
        if not data:
            raise OnlineImportError("The source returned an empty response.")
        if data.startswith(b"%PDF-"):
            suffix, mime = ".pdf", "application/pdf"
        elif content_type in ("text/plain", "text/html", "application/xhtml+xml"):
            if content_type != "text/plain":
                raise OnlineImportError("HTML pages are not imported as legal documents. Open the official page and select its PDF document link.")
            suffix, mime = ".txt", "text/plain"
        else:
            raise OnlineImportError("Only PDF and plain-text documents are accepted; received " + (content_type or "unknown content type") + ".")
        digest = hashlib.sha256(data).hexdigest()
        duplicate = self.conn.execute("SELECT document_id FROM documents WHERE file_hash=?", (digest,)).fetchone()
        if duplicate:
            raise OnlineImportError(f"Exact duplicate already exists as document #{duplicate['document_id']}.")
        source = self.conn.execute("SELECT source_id FROM sources WHERE source_name=? AND official_url=?", (name, info["host"])).fetchone()
        if source:
            source_id = source["source_id"]
        else:
            cur = self.conn.execute("""INSERT INTO sources(source_name,source_type,official_url,publisher,authority_level,jurisdiction,notes)
                VALUES(?,?,?,?,?,?,?)""", (name, info["kind"], "https://" + info["host"], info["publisher"], "official_publisher_host", info["jurisdiction"], "Host is allowlisted by the application. Individual document authenticity, legal currency and completeness still require review."))
            source_id = cur.lastrowid
        from app.core.paths import data_dir
        folder = data_dir() / "documents" / "online_sources"
        folder.mkdir(parents=True, exist_ok=True)
        filename = (title.strip() or Path(urlparse(final_url).path).name or "official_document")
        safe = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in filename).strip(" .")[:100] or "official_document"
        if not safe.lower().endswith(suffix): safe += suffix
        target = folder / f"{digest[:16]}_{safe}"
        target.write_bytes(data)
        text, pages, extraction = "", None, "not_supported"
        if suffix == ".txt":
            text = data.decode("utf-8", errors="replace"); extraction = "extracted"
        else:
            try:
                import fitz
                pdf = fitz.open(target); pages = len(pdf)
                text = "\\n\\n".join(page.get_text("text") for page in pdf)
                pdf.close(); extraction = "extracted" if text.strip() else "no_text_layer"
            except ImportError: extraction = "pymupdf_not_installed"
            except Exception: extraction = "extraction_error"
        doc_title = title.strip() or Path(safe).stem
        cur = self.conn.execute("""INSERT INTO documents(document_title,document_type,original_filename,stored_path,file_hash,mime_type,page_count,extraction_status,source_id,extracted_text)
            VALUES(?,?,?,?,?,?,?,?,?,?)""", (doc_title, document_type, safe, str(target), digest, mime, pages, extraction, source_id, text))
        doc_id = cur.lastrowid
        self.conn.execute("""INSERT INTO online_import_log(source_id,document_id,requested_url,final_url,http_status,content_type,content_length,sha256,result,notes)
            VALUES(?,?,?,?,?,?,?,?,?,?)""", (source_id, doc_id, requested, final_url, status, mime, len(data), digest, "imported", "Downloaded by explicit user action; source status remains subject to legal review."))
        self.conn.commit()
        return doc_id
