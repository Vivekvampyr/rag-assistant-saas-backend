from app.services.embeddings import embed_documents, embed_query


texts = [
    "Python is a programming language.",
    "FastAPI is a modern Python web framework.",
    "PostgreSQL is a relational database.",
]


embeddings = embed_documents(texts)

print("Number of embeddings:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))

query_embedding = embed_query(
    "What is Python?"
)

print("Query embedding dimension:", len(query_embedding))