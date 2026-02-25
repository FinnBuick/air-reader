"""
cache.py — SQLite-backed article cache.

Avoids re-fetching and re-extracting the same URL within the TTL window.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from typing import Optional
from dataclasses import dataclass

from air_reader import config


@dataclass
class CachedArticle:
    url: str
    title: Optional[str]
    author: Optional[str]
    date: Optional[str]
    text: str
    fetched_at: float


@contextmanager
def _db():
    conn = sqlite3.connect(config.CACHE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the cache table if it doesn't exist."""
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS article_cache (
                url          TEXT PRIMARY KEY,
                title        TEXT,
                author       TEXT,
                date         TEXT,
                extracted_text TEXT NOT NULL,
                fetched_at   REAL NOT NULL
            )
        """)


def get(url: str) -> Optional[CachedArticle]:
    """Return a cached article if it exists and has not expired."""
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM article_cache WHERE url = ?", (url,)
        ).fetchone()

    if row is None:
        return None

    age = time.time() - row["fetched_at"]
    if age > config.CACHE_TTL_SECONDS:
        return None

    return CachedArticle(
        url=row["url"],
        title=row["title"],
        author=row["author"],
        date=row["date"],
        text=row["extracted_text"],
        fetched_at=row["fetched_at"],
    )


def put(
    url: str,
    text: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    date: Optional[str] = None,
) -> None:
    """Insert or replace an article in the cache."""
    with _db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO article_cache
                (url, title, author, date, extracted_text, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (url, title, author, date, text, time.time()),
        )


def purge_expired() -> int:
    """Delete all expired cache entries. Returns the number of rows deleted."""
    cutoff = time.time() - config.CACHE_TTL_SECONDS
    with _db() as conn:
        cursor = conn.execute(
            "DELETE FROM article_cache WHERE fetched_at < ?", (cutoff,)
        )
        return cursor.rowcount
