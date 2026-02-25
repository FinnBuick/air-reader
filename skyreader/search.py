"""
search.py — Web search handler.

Supports two backends, selected via SEARCH_BACKEND env var:
  - "google"  : Google Custom Search API (100 free queries/day)
  - "searxng" : Self-hosted SearXNG instance (unlimited, private)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from skyreader import config

logger = logging.getLogger(__name__)

_MAX_RESULTS = 5


@dataclass
class SearchResult:
    rank: int
    title: str
    url: str
    snippet: Optional[str]


async def search(query: str) -> list[SearchResult]:
    """
    Run a web search and return up to _MAX_RESULTS results.

    Raises RuntimeError if the backend is misconfigured or the request fails.
    """
    backend = config.SEARCH_BACKEND.lower()
    if backend == "google":
        return await _google_search(query)
    elif backend == "searxng":
        return await _searxng_search(query)
    else:
        raise RuntimeError(f"Unknown SEARCH_BACKEND: {config.SEARCH_BACKEND!r}")


async def _google_search(query: str) -> list[SearchResult]:
    if not config.GOOGLE_CSE_KEY or not config.GOOGLE_CSE_CX:
        raise RuntimeError(
            "Google Custom Search requires GOOGLE_CSE_KEY and GOOGLE_CSE_CX env vars."
        )

    params = {
        "key": config.GOOGLE_CSE_KEY,
        "cx": config.GOOGLE_CSE_CX,
        "q": query,
        "num": _MAX_RESULTS,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://www.googleapis.com/customsearch/v1", params=params
        )
        resp.raise_for_status()
        data = resp.json()

    results: list[SearchResult] = []
    for i, item in enumerate(data.get("items", []), start=1):
        results.append(
            SearchResult(
                rank=i,
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet"),
            )
        )
    return results


async def _searxng_search(query: str) -> list[SearchResult]:
    params = {
        "q": query,
        "format": "json",
        "categories": "general",
    }
    url = config.SEARXNG_URL.rstrip("/") + "/search"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results: list[SearchResult] = []
    for i, item in enumerate(data.get("results", [])[:_MAX_RESULTS], start=1):
        results.append(
            SearchResult(
                rank=i,
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content"),
            )
        )
    return results


def format_results(query: str, results: list[SearchResult]) -> str:
    """Format search results as a WhatsApp-friendly string."""
    if not results:
        return f'🔍 No results found for "{query}".'

    lines = [f'🔍 Results for "{query}"\n']
    for r in results:
        domain = _domain(r.url)
        lines.append(f'{r.rank}. "{r.title}"')
        if domain:
            lines.append(f"   {domain}")
        lines.append(f"   → url: {r.url}")
        lines.append("")

    lines.append("Reply with a URL to read any article.")
    return "\n".join(lines)


def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""
