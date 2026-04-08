"""
vector_store.py — FAISS-based vector index for code chunk retrieval.
"""

import json
from pathlib import Path

import faiss
import numpy as np

import os
from google.cloud import storage

INDEX_DIR = Path("faiss_index")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

def _get_storage_client():
    """Initialize GCS client."""
    return storage.Client()

def get_repo_id(url: str) -> str:
    """Turn a GitHub URL into a safe, unique folder name (slug)."""
    return url.lower().rstrip("/").split("/")[-1].replace(".git", "").replace(".", "_")

def upload_to_gcs(local_path: Path, user_id: str, repo_id: str):
    """Upload index files to a scoped GCS path: {user_id}/{repo_id}/..."""
    if not BUCKET_NAME:
        print("⚠️ GCS_BUCKET_NAME not set, skipping upload.")
        return

    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    
    for filename in ["index.faiss", "chunks.json"]:
        blob = bucket.blob(f"{user_id}/{repo_id}/{filename}")
        blob.upload_from_filename(str(local_path / filename))
    print(f"🚀 Index uploaded to GCS: {user_id}/{repo_id}")

def download_from_gcs(local_path: Path, user_id: str, repo_id: str) -> bool:
    """Download index files from a scoped GCS path. Returns True if found."""
    if not BUCKET_NAME:
        print("⚠️ GCS_BUCKET_NAME not set, skipping download.")
        return False

    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    
    local_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Check if index exists before downloading
        index_blob = bucket.blob(f"{user_id}/{repo_id}/index.faiss")
        if not index_blob.exists():
            return False

        for filename in ["index.faiss", "chunks.json"]:
            blob = bucket.blob(f"{user_id}/{repo_id}/{filename}")
            blob.download_to_filename(str(local_path / filename))
        print(f"📥 Index downloaded from GCS: {user_id}/{repo_id}")
        return True
    except Exception as e:
        print(f"⚠️ GCS Download failed: {str(e)}")
        return False


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


def save_index(index: faiss.IndexFlatL2, chunks: list[dict], user_id: str, repo_url: str):
    """Persist the index locally and sync to the user's private cloud folder."""
    repo_id = get_repo_id(repo_url)
    path = INDEX_DIR / user_id / repo_id
    path.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(path / "index.faiss"))

    # Save chunk metadata
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
    print(f"💾 Index saved locally to {path}")
    
    # Sync to Cloud
    upload_to_gcs(path, user_id, repo_id)


def load_index(user_id: str, repo_url: str) -> tuple[faiss.IndexFlatL2, list[dict]]:
    """Load a scoped index from disk (after checking GCS)."""
    repo_id = get_repo_id(repo_url)
    path = INDEX_DIR / user_id / repo_id
    
    # Check GCS if local files are missing OR we want to ensure latest
    if not (path / "index.faiss").exists():
        found = download_from_gcs(path, user_id, repo_id)
        if not found:
            raise FileNotFoundError(f"Index not found for {repo_url}. Please ingest it first.")

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
