"""
repo_loader.py — Fetch repository contents recursively using the GitHub API.
"""

import os
import asyncio
import httpx
import ssl
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# File extensions we consider as "code" worth indexing
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".hpp", ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".kt",
    ".scala", ".lua", ".r", ".m", ".sql", ".sh", ".bash", ".zsh",
    ".ps1", ".bat", ".cmd", ".yaml", ".yml", ".toml", ".json",
    ".xml", ".html", ".css", ".scss", ".less", ".md", ".rst",
    ".dockerfile", ".tf", ".proto", ".graphql", ".vue", ".svelte",
}

# Directories to always skip (mostly for Git Trees API filtering)
SKIP_DIRS = {
    "node_modules", "venv", ".venv", "env", "__pycache__",
    "dist", "build", "vendor", "target", "bin", "obj",
}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def _get_ssl_context():
    """
    Create a secure SSL context using the system's native certificate store.
    If VERIFY_SSL is explicitly set to 'False' in .env, returns False to disable verification.
    """
    if os.getenv("VERIFY_SSL", "True").lower() == "false":
        print("⚠️ SSL Verification is DISABLED")
        return False
        
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        # Fallback to standard SSL context if truststore is missing
        return ssl.create_default_context()


def _parse_repo_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL."""
    parts = url.rstrip("/").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")
    return parts[-2], parts[-1].replace(".git", "")


async def fetch_repo_contents(repo_url: str):
    """
    Fetch all code files from a GitHub repository using the Git Trees API.
    
    Yields:
        Progress updates or the final list of code files.
    """
    owner, repo = _parse_repo_url(repo_url)
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    ssl_context = _get_ssl_context()

    async with httpx.AsyncClient(headers=headers, timeout=30.0, verify=ssl_context) as client:
        # 1. Get default branch
        repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
        resp = await client.get(repo_api_url)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch repo info: {resp.text}")
        default_branch = resp.json().get("default_branch", "main")

        # 2. Get recursive tree
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        resp = await client.get(tree_url)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch git tree: {resp.text}")
        
        tree_data = resp.json()
        if tree_data.get("truncated"):
            # Note: For massive repos, this might be an issue. 
            pass

        # 3. Filter for code files
        files_to_fetch = []
        for item in tree_data.get("tree", []):
            if item["type"] == "blob":
                path = item["path"]
                # Skip if any part of the path is in SKIP_DIRS
                if any(part in SKIP_DIRS for part in Path(path).parts):
                    continue
                
                ext = Path(path).suffix.lower()
                if ext in CODE_EXTENSIONS:
                    files_to_fetch.append(item)

        return files_to_fetch


async def download_file_content(client: httpx.AsyncClient, file_item: dict, semaphore: asyncio.Semaphore) -> dict:
    """Download the content of a single file from GitHub."""
    async with semaphore:
        url = file_item["url"]
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        
        import base64
        data = resp.json()
        try:
            # GitHub API returns base64 encoded content for blobs
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            return None

        return {
            "path": file_item["path"],
            "content": content,
            "language": Path(file_item["path"]).suffix.lstrip("."),
        }
