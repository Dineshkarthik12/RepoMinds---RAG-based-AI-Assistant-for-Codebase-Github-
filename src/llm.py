"""
llm.py — LLM-powered answer generation using OpenRouter (Asynchronous).
"""

import os

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client() -> AsyncOpenAI:
    """Create/return a reusable AsyncOpenAI client pointed at OpenRouter."""
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY not found. "
            "Create a .env file with OPENROUTER_API_KEY=your-key "
            "or set it as an environment variable."
        )
    _client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    return _client


SYSTEM_PROMPT = """\
You are **RepoMinds**, an expert code analyst. You answer developer questions
about a GitHub repository using the retrieved source-code snippets below.

Guidelines:
- Ground every claim in the provided code context.
- Reference file paths and line numbers when relevant.
- If the context is insufficient to answer fully, say so honestly.
- Use clear markdown formatting: headings, bullet points, and fenced code blocks.
"""


async def generate_answer(query: str, context_chunks: list[dict]) -> str:
    """Build a prompt from retrieved chunks and generate an LLM answer.

    Args:
        query: The user's natural-language question.
        context_chunks: list of chunk dicts from vector search.

    Returns:
        The LLM-generated answer string.
    """
    client = _get_client()

    # Build context block
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        header = (
            f"### Snippet {i} — `{chunk['file_path']}` "
            f"(lines {chunk['start_line']}–{chunk['end_line']})"
        )
        lang = chunk.get("language", "")
        context_parts.append(f"{header}\n```{lang}\n{chunk['text']}\n```")

    context_block = "\n\n".join(context_parts)

    user_prompt = (
        f"## Retrieved Code Context\n\n{context_block}\n\n"
        f"---\n\n## Developer Question\n\n{query}"
    )

    response = await client.chat.completions.create(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content
