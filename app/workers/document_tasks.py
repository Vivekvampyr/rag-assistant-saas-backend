from pathlib import Path
from app.core.database import SessionLocal
from app.models.document import Document
from app.services.ingestion import process_document
from app.workers.celery_app import celery_app

@celery_app.task(
    bind=True,
    name="process_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_document_task(
    self,
    document_id: int,
    file_path: str,
):
    """
    Process a document in a background worker.
    """

    db = SessionLocal()

    try:
        document = db.get(Document, document_id)

        if document is None:
            raise ValueError(
                f"Document {document_id} not found."
            )

        process_document(
            document=document,
            db=db,
            file_path=Path(file_path),
        )

        return {
            "document_id": document_id,
            "status": "COMPLETED",
        }

    finally:
        db.close()