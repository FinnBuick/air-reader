"""
fetcher.py — Web content fetching and extraction.

Primary path: trafilatura (pure-HTTP).
Fallback path: Playwright headless browser for JS-heavy SPAs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import trafilatura
import trafilatura.settings
import trafilatura.utils

from air_reader import cache, config

logger = logging.getLogger(__name__)


@dataclass
class Article:
    url: str
    title: Optional[str]
    author: Optional[str]
    date: Optional[str]
    text: str
    from_cache: bool = False


class FetchError(Exception):
    """Raised when an article cannot be fetched or extracted."""


def _extract(html: str, url: str) -> Optional[str]:
    return trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
        deduplicate=True,
        output_format="txt",
    )


def _extract_metadata(html: str):
    return trafilatura.extract_metadata(html)


def _fetch_trafilatura(url: str) -> Optional[str]:
    """Download raw HTML via trafilatura's built-in fetcher."""
    return trafilatura.fetch_url(url)


async def _fetch_playwright(url: str) -> str:
    """Render a page with a headless Chromium browser and return its HTML."""
    from playwright.async_api import async_playwright  # lazy import

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            url,
            wait_until="networkidle",
            timeout=config.PLAYWRIGHT_TIMEOUT_MS,
        )
        html = await page.content()
        await browser.close()
    return html


async def fetch(url: str) -> Article:
    """
    Fetch and extract an article from *url*.

    Check the cache first; if not cached, attempt trafilatura then Playwright.
    Raises FetchError if extraction fails.
    """
    # --- Cache hit ---
    cached = cache.get(url)
    if cached:
        logger.info("Cache hit for %s", url)
        return Article(
            url=cached.url,
            title=cached.title,
            author=cached.author,
            date=cached.date,
            text=cached.text,
            from_cache=True,
        )

    # --- Primary: trafilatura ---
    html = _fetch_trafilatura(url)
    text: Optional[str] = None
    if html:
        text = _extract(html, url)

    # --- Fallback: Playwright ---
    if not text or len(text) < config.MIN_CONTENT_LENGTH:
        logger.info("trafilatura returned short/no content for %s, trying Playwright", url)
        try:
            html = await _fetch_playwright(url)
            text = _extract(html, url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Playwright fallback failed for %s: %s", url, exc)
            # Keep whatever trafilatura returned (could still be None)

    if not text:
        raise FetchError(f"Could not extract content from {url}")

    # Extract metadata from last successful HTML
    meta = _extract_metadata(html) if html else None
    title = meta.title if meta else None
    author = meta.author if meta else None
    date = meta.date if meta else None

    # Cache result
    cache.put(url=url, text=text, title=title, author=author, date=date)

    return Article(url=url, title=title, author=author, date=date, text=text)
