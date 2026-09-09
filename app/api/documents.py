from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document
from app.workers.document_tasks import process_document_task
from sqlalchemy import select

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

ALLOWED_EXTENSIONS = {".pdf"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    unique_filename = f"{uuid4().hex}{extension}"
    file_path = upload_dir / unique_filename

    file_path.write_bytes(content)

    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        file_type=extension.lstrip("."),
        file_size=len(content),
        status="PROCESSING",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Queue background processing.
    process_document_task.delay(
        document_id=document.id,
        file_path=str(file_path),
    )

    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
    }


@router.get("/{document_id}")
def get_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "status": document.status,
        "total_pages": document.total_pages,
        "total_chunks": document.total_chunks,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }

@router.get("")
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = db.scalars(
        select(Document).where(Document.user_id == current_user.id).order_by(
            Document.created_at.desc()
        )
    ).all()

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "status": document.status,
            "total_pages": document.total_pages,
            "total_chunks": document.total_chunks,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }
        for document in documents
    ]