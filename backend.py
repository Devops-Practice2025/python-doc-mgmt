import os
import shutil
from pathlib import Path
from uuid import uuid4
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from models import Document, SessionLocal, init_db

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads")).resolve()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg"}
app = FastAPI(title="Document Management API", version="2.0.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def serialize(doc: Document):
    return {"id": doc.id, "title": doc.title, "category": doc.category,
            "filename": doc.original_filename, "content_type": doc.content_type,
            "size_bytes": doc.size_bytes, "created_at": doc.created_at.isoformat()}

@app.on_event("startup")
def startup():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()

@app.get("/healthz")
def healthz(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok"}

@app.get("/api/documents")
def list_documents(q: str = "", category: str = "", db: Session = Depends(get_db)):
    stmt = select(Document).order_by(Document.created_at.desc())
    if q.strip():
        term = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Document.title).like(term), func.lower(Document.original_filename).like(term)))
    if category.strip():
        stmt = stmt.where(Document.category == category.strip())
    return [serialize(d) for d in db.scalars(stmt).all()]

@app.post("/api/documents/upload", status_code=status.HTTP_201_CREATED)
def upload_document(title: str = Form(...), category: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    title, category = title.strip(), category.strip()
    original = Path(file.filename or "").name
    ext = Path(original).suffix.lower()
    if not title or len(title) > 200: raise HTTPException(400, "Title must contain 1-200 characters")
    if not category or len(category) > 100: raise HTTPException(400, "Category must contain 1-100 characters")
    if not original or ext not in ALLOWED_EXTENSIONS: raise HTTPException(400, "Unsupported or missing file extension")
    storage_name = f"{uuid4().hex}{ext}"
    target = (UPLOAD_DIR / storage_name).resolve()
    if target.parent != UPLOAD_DIR: raise HTTPException(400, "Invalid filename")
    size = 0
    try:
        with target.open("xb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES: raise HTTPException(413, "File exceeds upload limit")
                out.write(chunk)
        if size == 0: raise HTTPException(400, "Empty files are not allowed")
        doc = Document(title=title, category=category, original_filename=original,
                       storage_filename=storage_name, content_type=file.content_type or "application/octet-stream", size_bytes=size)
        db.add(doc); db.commit(); db.refresh(doc)
        return serialize(doc)
    except Exception:
        db.rollback(); target.unlink(missing_ok=True); raise
    finally:
        file.file.close()

@app.get("/api/documents/{document_id}/download")
def download(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc: raise HTTPException(404, "Document not found")
    path = (UPLOAD_DIR / doc.storage_filename).resolve()
    if path.parent != UPLOAD_DIR or not path.is_file(): raise HTTPException(404, "Stored file not found")
    return FileResponse(path, media_type=doc.content_type, filename=doc.original_filename)

@app.delete("/api/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc: raise HTTPException(404, "Document not found")
    path = (UPLOAD_DIR / doc.storage_filename).resolve()
    db.delete(doc); db.commit()
    if path.parent == UPLOAD_DIR: path.unlink(missing_ok=True)
