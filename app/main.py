from fastapi import FastAPI

from app.core.database import Base, engine

# Import models so SQLAlchemy knows about them
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.api import documents
from app.api import chat
from app.api import auth
from app.models.user import User

app = FastAPI(
    title="RAG Knowledge Assistant",
)

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(auth.router)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "message": "RAG Knowledge Assistant API"
    }