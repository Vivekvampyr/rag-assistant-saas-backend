from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model once and reuse it.
    """
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple document chunks.
    """

    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return np.asarray(embeddings, dtype=np.float32).tolist()


def embed_query(text: str) -> list[float]:
    """
    Generate an embedding for a user's search query.
    """

    if not text or not text.strip():
        raise ValueError("Query text cannot be empty.")

    model = get_embedding_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return np.asarray(embedding, dtype=np.float32).tolist()