"""
vector_store.py — FAISS-based vector index for code chunk retrieval.
"""

import json
from pathlib import Path

import faiss
import numpy as np

INDEX_DIR = Path("faiss_index")


def build_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """Build a FAISS L2 index from embedding vectors.

    Args:
        embeddings: np.ndarray of shape (n, dim).

    Returns:
        A populated FAISS index.
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    print(f"📦 FAISS index built: {index.ntotal} vectors, dim={dim}")
    return index


def save_index(index: faiss.IndexFlatL2, chunks: list[dict], path: Path | None = None):
    """Persist the FAISS index and chunk metadata to disk."""
    path = path or INDEX_DIR
    path.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(path / "index.faiss"))

    # Save chunk metadata (everything except full text for smaller file)
    meta = []
    for c in chunks:
        meta.append({
            "text": c["text"],
            "file_path": c["file_path"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "language": c.get("language", ""),
        })

    (path / "chunks.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"💾 Index saved to {path}")


def load_index(path: Path | None = None) -> tuple[faiss.IndexFlatL2, list[dict]]:
    """Load a FAISS index and chunk metadata from disk."""
    path = path or INDEX_DIR
    index = faiss.read_index(str(path / "index.faiss"))
    chunks = json.loads((path / "chunks.json").read_text(encoding="utf-8"))
    print(f"📂 Loaded index: {index.ntotal} vectors, {len(chunks)} chunks")
    return index, chunks


def search(
    index: faiss.IndexFlatL2,
    query_embedding: np.ndarray,
    chunks: list[dict],
    k: int = 5,
) -> list[dict]:
    """Search the index for the top-k most similar chunks.

    Returns:
        list of chunk dicts, each augmented with a 'score' key.
    """
    distances, indices = index.search(query_embedding, k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        chunk = dict(chunks[idx])
        chunk["score"] = float(dist)
        results.append(chunk)
    return results
