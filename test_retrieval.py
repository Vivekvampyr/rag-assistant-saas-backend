from app.core.database import SessionLocal
from app.services.retrieval import retrieve_document_chunks


db = SessionLocal()

try:
    results = retrieve_document_chunks(
        query="Who is Vivek?",
        db=db,
        top_k=5,
    )

    for result in results:
        print("=" * 70)
        print("Document:", result["filename"])
        print("Page:", result["page_number"])
        print("Score:", result["score"])
        print("Content:")
        print(result["content"])

finally:
    db.close()