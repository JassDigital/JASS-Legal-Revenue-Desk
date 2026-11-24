from pathlib import Path
import hashlib, shutil, mimetypes
from app.core.paths import data_dir

class DocumentImportError(Exception): pass

class DocumentImportService:
    def __init__(self, conn): self.conn = conn
    def import_file(self, source_path, document_type="Other"):
        source = Path(source_path)
        if not source.is_file(): raise DocumentImportError("Selected file does not exist.")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        duplicate = self.conn.execute("SELECT document_id FROM documents WHERE file_hash=?", (digest,)).fetchone()
        if duplicate: raise DocumentImportError(f"Exact duplicate already imported as document #{duplicate['document_id']}.")
        folder = data_dir() / "documents" / document_type.lower().replace(" ","_")
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{digest[:16]}_{source.name}"
        shutil.copy2(source, target)
        text, pages, status = "", None, "not_supported"
        mime = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        if source.suffix.lower() == ".txt":
            text = source.read_text(encoding="utf-8", errors="replace"); status = "extracted"
        elif source.suffix.lower() == ".pdf":
            try:
                import fitz
                pdf = fitz.open(target); pages = len(pdf)
                text = "\\n\\n".join(page.get_text("text") for page in pdf)
                pdf.close(); status = "extracted" if text.strip() else "no_text_layer"
            except ImportError: status = "pymupdf_not_installed"
            except Exception: status = "extraction_error"
        cur = self.conn.execute("""INSERT INTO documents
            (document_title,document_type,original_filename,stored_path,file_hash,mime_type,
             page_count,extraction_status,extracted_text)
             VALUES(?,?,?,?,?,?,?,?,?)""",
             (source.stem,document_type,source.name,str(target),digest,mime,pages,status,text))
        doc_id = cur.lastrowid
        self.conn.execute("""INSERT INTO document_import_log
            (document_id,original_path,result,message) VALUES(?,?,?,?)""",
            (doc_id,str(source),"success",status))
        self.conn.commit()
        return doc_id
