from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document
from app.services.ingestion import process_document


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

ALLOWED_EXTENSIONS = {".pdf"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
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

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # --------------------------------------------------
    # Save original file
    # --------------------------------------------------

    unique_filename = f"{uuid4().hex}{extension}"
    file_path = upload_dir / unique_filename

    file_path.write_bytes(content)

    # --------------------------------------------------
    # Create document record
    # --------------------------------------------------

    document = Document(
        filename=file.filename,
        file_type=extension.lstrip("."),
        file_size=len(content),
        status="PROCESSING",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # --------------------------------------------------
    # Process document
    # --------------------------------------------------

    try:

        process_document(
            document=document,
            db=db,
            file_path=file_path,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(exc)}",
        )

    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
        "total_pages": document.total_pages,
        "total_chunks": document.total_chunks,
    }