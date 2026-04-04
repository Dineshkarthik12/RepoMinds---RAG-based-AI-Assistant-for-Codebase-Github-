"""
pipeline.py — End-to-end orchestration: ingest a repo and query it.
"""

from pathlib import Path

from .repo_loader import clone_repo, extract_code_files
from .chunker import chunk_all_files
from .embedder import embed_chunks, embed_query
from .vector_store import build_index, save_index, load_index, search
from .llm import generate_answer


def ingest(repo_url: str):
    """Clone a repo, chunk its code, embed, and build a FAISS index.

    Args:
        repo_url: GitHub repository URL.

    Yields:
        dict: Progress updates or final stats dict.
    """
    def _progress(stage, detail=""):
        return {"type": "progress", "stage": stage, "detail": detail}

    # 1. Clone
    yield _progress("clone", f"Cloning {repo_url}…")
    repo_path = clone_repo(repo_url)
    repo_name = repo_path.name

    # 2. Extract code files
    yield _progress("extract", "Extracting code files…")
    code_files = extract_code_files(repo_path)
    if not code_files:
        raise ValueError("No code files found in the repository.")

    # 3. Chunk
    yield _progress("chunk", f"Chunking {len(code_files)} files…")
    chunks = chunk_all_files(code_files)

    # 4. Embed
    yield _progress("embed", f"Embedding {len(chunks)} chunks…")
    embeddings = embed_chunks(chunks)

    # 5. Build & save FAISS index
    yield _progress("index", "Building FAISS index…")
    index = build_index(embeddings)
    save_index(index, chunks)

    yield _progress("done", "✅ Repository ingested successfully!")

    yield {
        "type": "result",
        "stats": {
            "repo_name": repo_name,
            "num_files": len(code_files),
            "num_chunks": len(chunks),
            "index_size": index.ntotal,
        }
    }


def query(question: str, k: int = 5) -> dict:
    """Answer a developer question using the indexed repository.

    Args:
        question: natural-language question.
        k: number of chunks to retrieve.

    Returns:
        dict with {answer: str, sources: list[dict]}
    """
    # Load persisted index
    index, chunks = load_index()

    # Embed the question
    q_embedding = embed_query(question)

    # Retrieve top-k chunks
    results = search(index, q_embedding, chunks, k=k)

    # Generate answer via LLM
    answer = generate_answer(question, results)

    return {
        "answer": answer,
        "sources": results,
    }
