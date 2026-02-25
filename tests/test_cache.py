"""Tests for air_reader.cache — SQLite article cache."""

import time
from unittest.mock import patch

from air_reader import cache, config


class TestCachePutGet:
    def test_put_and_get(self, tmp_cache_db):
        cache.put(url="https://example.com", text="body text", title="Title")
        result = cache.get("https://example.com")
        assert result is not None
        assert result.url == "https://example.com"
        assert result.text == "body text"
        assert result.title == "Title"

    def test_get_missing_returns_none(self, tmp_cache_db):
        result = cache.get("https://nonexistent.com")
        assert result is None

    def test_expired_entry_returns_none(self, tmp_cache_db, monkeypatch):
        cache.put(url="https://example.com", text="body")
        # Simulate TTL expiry
        monkeypatch.setattr(config, "CACHE_TTL_SECONDS", 0)
        result = cache.get("https://example.com")
        assert result is None

    def test_put_replaces_existing(self, tmp_cache_db):
        cache.put(url="https://example.com", text="old")
        cache.put(url="https://example.com", text="new")
        result = cache.get("https://example.com")
        assert result.text == "new"


class TestPurgeExpired:
    def test_purge_removes_old_entries(self, tmp_cache_db, monkeypatch):
        cache.put(url="https://old.com", text="old")
        # Make it expired
        monkeypatch.setattr(config, "CACHE_TTL_SECONDS", 0)
        deleted = cache.purge_expired()
        assert deleted >= 1
        # Verify it's gone
        monkeypatch.setattr(config, "CACHE_TTL_SECONDS", 86400)
        assert cache.get("https://old.com") is None

    def test_purge_keeps_fresh_entries(self, tmp_cache_db):
        cache.put(url="https://fresh.com", text="fresh")
        deleted = cache.purge_expired()
        assert deleted == 0
        assert cache.get("https://fresh.com") is not None
