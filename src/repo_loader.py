"""
repo_loader.py — Clone GitHub repositories and extract code files.
"""

import os
import stat
import shutil
from pathlib import Path
from git import Repo


def _force_remove_readonly(func, path, _exc_info):
    """Handle read-only files on Windows (e.g. .git pack files)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


# File extensions we consider as "code" worth indexing
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".hpp", ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".kt",
    ".scala", ".lua", ".r", ".m", ".sql", ".sh", ".bash", ".zsh",
    ".ps1", ".bat", ".cmd", ".yaml", ".yml", ".toml", ".json",
    ".xml", ".html", ".css", ".scss", ".less", ".md", ".rst",
    ".dockerfile", ".tf", ".proto", ".graphql", ".vue", ".svelte",
}

# Directories to always skip
SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".next", ".nuxt", "vendor", "target", "bin", "obj",
    ".idea", ".vscode", ".gradle", ".settings",
}

REPOS_DIR = Path("repos")


def clone_repo(github_url: str) -> Path:
    """Clone a GitHub repository and return its local path.

    If the repo already exists locally, it will be re-cloned fresh.
    """
    # Derive repo name from URL
    repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
    dest = REPOS_DIR / repo_name

    if dest.exists():
        shutil.rmtree(dest, onerror=_force_remove_readonly)

    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📥 Cloning {github_url} → {dest}")
    Repo.clone_from(github_url, str(dest), depth=1)  # shallow clone for speed
    print("✅ Clone complete")
    return dest


def extract_code_files(repo_path: Path) -> list[dict]:
    """Walk the repo and return a list of code-file dicts.

    Returns:
        list of {"path": relative_path, "content": file_text, "language": ext}
    """
    files = []
    repo_path = Path(repo_path)

    for root, dirs, filenames in os.walk(repo_path):
        # Prune directories we don't care about (modifies walk in-place)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in CODE_EXTENSIONS:
                continue

            full_path = Path(root) / fname
            rel_path = full_path.relative_to(repo_path).as_posix()

            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if not content.strip():
                continue

            files.append({
                "path": rel_path,
                "content": content,
                "language": ext.lstrip("."),
            })

    print(f"📄 Extracted {len(files)} code files")
    return files
