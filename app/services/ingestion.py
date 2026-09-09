from pathlib import Path

from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.services.chunker import chunk_pages
from app.services.embeddings import embed_documents
from app.services.parser import extract_pdf_text


def process_document(
    document: Document,
    db: Session,
    file_path: str | Path,
) -> None:
    """
    Complete document ingestion pipeline:

    PDF
      -> text extraction
      -> chunking
      -> embeddings
      -> database
    """

    try:
        # --------------------------------------------------
        # 1. Extract text page-by-page
        # --------------------------------------------------
        pages = extract_pdf_text(file_path)

        document.total_pages = len(pages)

        # --------------------------------------------------
        # 2. Chunk extracted text
        # --------------------------------------------------
        chunks = chunk_pages(
            pages,
            chunk_size=800,
            overlap=100,
        )

        if not chunks:
            raise ValueError(
                "No text could be extracted from the document."
            )

        # --------------------------------------------------
        # 3. Generate embeddings
        # --------------------------------------------------
        texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = embed_documents(texts)

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding count does not match chunk count."
            )

        # --------------------------------------------------
        # 4. Create database chunk records
        # --------------------------------------------------
        document_chunks = []

        for chunk, embedding in zip(chunks, embeddings):

            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"],
                content=chunk["content"],
                token_count=None,
                embedding=embedding,
            )

            document_chunks.append(document_chunk)

        # --------------------------------------------------
        # 5. Store chunks in PostgreSQL
        # --------------------------------------------------
        db.add_all(document_chunks)

        document.total_chunks = len(document_chunks)
        document.status = "COMPLETED"

        db.commit()

    except Exception:
        db.rollback()

        document.status = "FAILED"

        db.commit()

        raise