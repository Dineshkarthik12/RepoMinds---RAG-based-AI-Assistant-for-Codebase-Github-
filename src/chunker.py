"""
chunker.py — Split code files into overlapping, semantically meaningful chunks.
"""

import re


# Regex patterns that indicate logical boundaries in code
BOUNDARY_PATTERNS = [
    re.compile(r"^\s*(def |async def )", re.MULTILINE),       # Python functions
    re.compile(r"^\s*class\s+\w+", re.MULTILINE),             # Class definitions
    re.compile(r"^\s*(function |const |let |var )\w+", re.MULTILINE),  # JS/TS
    re.compile(r"^\s*(public |private |protected |static )", re.MULTILINE),  # Java/C#
    re.compile(r"^\s*func\s+\w+", re.MULTILINE),              # Go
    re.compile(r"^\s*(fn |pub fn |impl )", re.MULTILINE),     # Rust
]


def _find_boundaries(lines: list[str]) -> list[int]:
    """Return line indices that are logical code boundaries."""
    boundaries = set()
    for i, line in enumerate(lines):
        for pattern in BOUNDARY_PATTERNS:
            if pattern.match(line):
                boundaries.add(i)
                break
    return sorted(boundaries)


def chunk_code(
    file_path: str,
    content: str,
    max_lines: int = 60,
    overlap_lines: int = 10,
) -> list[dict]:
    """Split a code file into overlapping chunks.

    Each chunk is a dict with:
      - text:       the chunk text
      - file_path:  original file path
      - start_line: 1-indexed start line
      - end_line:   1-indexed end line
      - language:   file extension (for display)

    The chunker tries to split at function / class boundaries when possible,
    falling back to a sliding-window approach.
    """
    lines = content.splitlines(keepends=True)
    total = len(lines)

    if total == 0:
        return []

    language = file_path.rsplit(".", 1)[-1] if "." in file_path else ""

    # For small files, treat the whole file as one chunk
    if total <= max_lines:
        return [{
            "text": content,
            "file_path": file_path,
            "start_line": 1,
            "end_line": total,
            "language": language,
        }]

    boundaries = _find_boundaries(lines)
    chunks = []
    start = 0

    while start < total:
        end = min(start + max_lines, total)

        # Try to snap the end to a code boundary for cleaner splits
        if end < total:
            # Find the last boundary that falls within our window
            candidates = [b for b in boundaries if start + max_lines // 2 < b <= end]
            if candidates:
                end = candidates[-1]

        chunk_text = "".join(lines[start:end])
        chunks.append({
            "text": chunk_text,
            "file_path": file_path,
            "start_line": start + 1,
            "end_line": end,
            "language": language,
        })

        # Advance with overlap
        start = max(start + 1, end - overlap_lines)

    return chunks


def chunk_all_files(code_files: list[dict], max_lines: int = 60, overlap_lines: int = 10) -> list[dict]:
    """Chunk every file in the list and return a flat list of all chunks."""
    all_chunks = []
    for f in code_files:
        file_chunks = chunk_code(f["path"], f["content"], max_lines, overlap_lines)
        all_chunks.extend(file_chunks)
    print(f"🔪 Created {len(all_chunks)} chunks from {len(code_files)} files")
    return all_chunks
