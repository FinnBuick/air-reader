"""
fetcher.py — Web content fetching and extraction.

Primary path: trafilatura (pure-HTTP).
Fallback path: Playwright headless browser for JS-heavy SPAs.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

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


# ---------------------------------------------------------------------------
# SSRF protection
# ---------------------------------------------------------------------------

def validate_url(url: str) -> str:
    """
    Validate that *url* is a safe, public HTTP(S) URL.

    Raises FetchError for disallowed schemes, private/reserved IPs, and
    link-local or loopback addresses.
    """
    if not url:
        raise FetchError("Empty URL")

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise FetchError(f"Disallowed URL scheme: {parsed.scheme!r}")

    hostname = parsed.hostname
    if not hostname:
        raise FetchError("URL has no host")

    # Resolve hostname → reject private / reserved IPs
    if hostname in ("localhost",):
        raise FetchError(f"URL targets private/reserved address: {hostname}")

    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        # It's a DNS name — resolve it to check the IP
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            if resolved:
                addr = ipaddress.ip_address(resolved[0][4][0])
            else:
                raise FetchError(f"Cannot resolve host: {hostname}")
        except socket.gaierror:
            raise FetchError(f"Cannot resolve host: {hostname}")

    if addr.is_private or addr.is_reserved or addr.is_loopback or addr.is_link_local:
        raise FetchError(f"URL targets private/reserved address: {addr}")

    return url


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

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
        try:
            page = await browser.new_page()
            await page.goto(
                url,
                wait_until="networkidle",
                timeout=config.PLAYWRIGHT_TIMEOUT_MS,
            )
            html = await page.content()
        finally:
            await browser.close()
    return html


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch(url: str) -> Article:
    """
    Fetch and extract an article from *url*.

    Validates the URL against SSRF, checks the cache, then attempts
    trafilatura followed by Playwright.  Raises FetchError on failure.
    """
    # --- SSRF guard ---
    validate_url(url)

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
