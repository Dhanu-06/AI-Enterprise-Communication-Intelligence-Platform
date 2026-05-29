"""ChromaDB collection configuration."""

COLLECTION_METADATA = {
    "hnsw:space": "cosine",
    "description": "Email semantic embeddings for similarity search and recommendations",
}

EMBEDDING_BATCH_SIZE = 64
