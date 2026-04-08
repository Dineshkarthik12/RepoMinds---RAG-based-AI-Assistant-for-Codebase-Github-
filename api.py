from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

from src.pipeline import ingest, query

app = FastAPI(title="RepoMinds API", description="Backend for the RepoMinds React app")

# Add CORS middleware to allow the React frontend (usually port 5173) 
# and the Streamlit frontend (if still used) to connect.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for cloud deployment stability
 # For development, allowing all; can be restricted later.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    repo_url: str
    user_id: str

class QueryRequest(BaseModel):
    question: str
    user_id: str
    repo_url: str
    k: int = 5

@app.post("/ingest")
async def api_ingest(req: IngestRequest):
    """
    Ingest a GitHub repository via API. Returns a streaming response of JSON lines 
    representing progress updates, ending with the final stat block.
    """
    if not req.repo_url or not req.repo_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL provided.")

    async def event_stream():
        try:
            async for event in ingest(req.repo_url, user_id=req.user_id):
                yield json.dumps(event) + "\n"
        except Exception as e:
            # Yield error event so the frontend can catch it
            yield json.dumps({"type": "error", "detail": str(e)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

@app.post("/query")
async def api_query(req: QueryRequest):
    """
    Query the indexed repository using the scoped user_id and repo_url.
    """
    async def event_stream():
        try:
            async for event in query(req.question, user_id=req.user_id, repo_url=req.repo_url, k=req.k):
                yield json.dumps(event) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "detail": str(e)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
