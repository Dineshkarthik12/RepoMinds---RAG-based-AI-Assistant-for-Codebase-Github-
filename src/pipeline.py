"""
pipeline.py — End-to-end orchestration: ingest a repo and query it (Asynchronous).
"""

import asyncio
import ssl
import httpx
from pathlib import Path

from .repo_loader import fetch_repo_contents, download_file_content, _get_ssl_context
from .chunker import chunk_all_files
from .embedder import embed_chunks, embed_query
from .vector_store import build_index, save_index, load_index, search
from .llm import generate_answer

async def ingest(repo_url: str):
    """Fetch repo contents via API, chunk, embed, and build a FAISS index.

    Args:
        repo_url: GitHub repository URL.

    Yields:
        dict: Progress updates or final stats dict.
    """
    def _progress(stage, detail=""):
        return {"type": "progress", "stage": stage, "detail": detail}

    # 1. Fetch File List Metadata
    yield _progress("fetch_metadata", f"Fetching file list from {repo_url}…")
    try:
        files_metadata = await fetch_repo_contents(repo_url)
    except Exception as e:
        yield {"type": "error", "detail": f"Failed to fetch metadata: {str(e)}"}
        return

    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    num_files = len(files_metadata)
    yield _progress("extract", f"Found {num_files} code files. Starting download…")

    # 2. Download File Contents (with concurrency control)
    import os
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    ssl_context = _get_ssl_context()
    semaphore = asyncio.Semaphore(10) # Max 10 concurrent requests
    all_chunks = []
    
    async with httpx.AsyncClient(headers=headers, timeout=30.0, verify=ssl_context) as client:
        tasks = [download_file_content(client, f, semaphore) for f in files_metadata]
        
        # We process downloads and chunking
        downloaded_count = 0
        for future in asyncio.as_completed(tasks):
            file_data = await future
            if file_data:
                downloaded_count += 1
                from .chunker import chunk_code
                file_chunks = chunk_code(file_data["path"], file_data["content"])
                all_chunks.extend(file_chunks)
                
                if downloaded_count % 20 == 0:
                    yield _progress("download", f"Downloaded {downloaded_count}/{num_files} files…")

    if not all_chunks:
        yield {"type": "error", "detail": "No code content found to index."}
        return

    # 3. Embed
    yield _progress("embed", f"Embedding {len(all_chunks)} chunks…")
    embeddings = await embed_chunks(all_chunks)

    # 4. Build & save FAISS index
    yield _progress("index", "Building FAISS index…")
    index = await asyncio.to_thread(build_index, embeddings)
    await asyncio.to_thread(save_index, index, all_chunks)

    yield _progress("done", "✅ Repository ingested successfully via GitHub API!")

    yield {
        "type": "result",
        "stats": {
            "repo_name": repo_name,
            "num_files": num_files,
            "num_chunks": len(all_chunks),
            "index_size": index.ntotal,
        }
    }


async def query(question: str, k: int = 5) -> dict:
    """Answer a developer question using the indexed repository (Asynchronous).

    Args:
        question: natural-language question.
        k: number of chunks to retrieve.

    Returns:
        dict with {answer: str, sources: list[dict]}
    """
    # Load persisted index (Disk I/O)
    index, chunks = await asyncio.to_thread(load_index)

    # Embed the question
    q_embedding = await embed_query(question)

    # Retrieve top-k chunks
    results = await asyncio.to_thread(search, index, q_embedding, chunks, k=k)

    # Generate answer via LLM (Network I/O)
    answer = await generate_answer(question, results)

    return {
        "answer": answer,
        "sources": results,
    }
