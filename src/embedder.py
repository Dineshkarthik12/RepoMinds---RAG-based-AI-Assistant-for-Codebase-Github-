"""
embedder.py — Generate embeddings using sentence-transformers.
"""

import numpy as np
# Singleton model instance to avoid reloading on every call
_model = None
MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        print(f"🧠 Loading embedding model: {MODEL_NAME}")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
        print("✅ Model loaded")
    return _model


def embed_chunks(chunks: list[dict], batch_size: int = 64) -> np.ndarray:
    """Encode a list of code chunks into embedding vectors.

    Args:
        chunks: list of chunk dicts (must have a 'text' key).
        batch_size: encoding batch size.

    Returns:
        np.ndarray of shape (len(chunks), embedding_dim).
    """
    model = _get_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    return np.array(embeddings, dtype="float32")


def embed_query(query: str) -> np.ndarray:
    """Encode a single user query into an embedding vector.

    Returns:
        np.ndarray of shape (1, embedding_dim).
    """
    model = _get_model()
    embedding = model.encode([query])
    return np.array(embedding, dtype="float32")
