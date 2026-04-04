from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from src.pipeline import ingest, query

app = FastAPI(title="RepoMinds API", description="Backend for the RepoMinds Streamlit app")

class IngestRequest(BaseModel):
    repo_url: str

class QueryRequest(BaseModel):
    question: str
    k: int = 5

@app.post("/ingest")
def api_ingest(req: IngestRequest):
    """
    Ingest a GitHub repository. Returns a streaming response of JSON lines 
    representing progress updates, ending with the final stat block.
    """
    if not req.repo_url or not req.repo_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL provided.")

    def event_stream():
        try:
            for event in ingest(req.repo_url):
                yield json.dumps(event) + "\n"
        except Exception as e:
            # Yield error event so the frontend can catch it
            yield json.dumps({"type": "error", "detail": str(e)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

@app.post("/query")
def api_query(req: QueryRequest):
    """
    Query the indexed repository.
    """
    try:
        result = query(req.question, k=req.k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
