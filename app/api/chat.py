from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.services.generation import generate_answer
from app.services.retrieval import retrieve_document_chunks

from app.core.security import get_current_user
from app.models.document import Document
from app.models.user import User

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: int | None = None


@router.post("/ask")
def ask_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if request.document_id is not None:
        document = db.scalar(
            select(Document).where(
                Document.id == request.document_id,
                Document.user_id == current_user.id,
            )
        )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )
    
    try:
        matches = retrieve_document_chunks(
            query=request.question,
            db=db,
            user_id=current_user.id,
            top_k=5,
            similarity_threshold=0.40,
            document_id=request.document_id,
        )

        if not matches:
            return {
                "answer": (
                    "I couldn't find that information "
                    "in the uploaded documents."
                ),
                "sources": [],
            }

        answer = generate_answer(
            question=request.question,
            matches=matches,
        )

        sources = [
            {
                "chunk_id": match["chunk_id"],
                "document_id": match["document_id"],
                "filename": match["filename"],
                "page_number": match["page_number"],
                "score": round(match["score"], 4),
            }
            for match in matches
        ]

        return {
            "answer": answer,
            "sources": sources,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(exc)}",
        )