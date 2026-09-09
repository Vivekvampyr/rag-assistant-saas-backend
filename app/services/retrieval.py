from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.embeddings import embed_query


def retrieve_document_chunks(
    query: str,
    db: Session,
    top_k: int = 5,
    similarity_threshold: float = 0.40,
    document_id: int | None = None,
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a query.

    Optionally restrict retrieval to a single document.
    """

    query_embedding = embed_query(query)

    sql = """
        SELECT
            dc.id,
            dc.document_id,
            dc.chunk_index,
            dc.page_number,
            dc.content,
            d.filename,
            1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM document_chunks dc
        JOIN documents d
            ON d.id = dc.document_id
        WHERE d.status = 'COMPLETED'
        """

    params = {
        "embedding": query_embedding,
        "top_k": top_k,
    }

    if document_id is not None:
        sql += """
            AND dc.document_id = :document_id
        """
        params["document_id"] = document_id

    sql += """
        ORDER BY dc.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """

    result = db.execute(text(sql), params)

    matches = []

    for row in result:
        score = float(row.similarity)

        if score < similarity_threshold:
            continue

        matches.append(
            {
                "chunk_id": row.id,
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "page_number": row.page_number,
                "content": row.content,
                "filename": row.filename,
                "score": score,
            }
        )

    return matches