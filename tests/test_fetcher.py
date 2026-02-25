"""Tests for air_reader.fetcher — URL validation & SSRF protection."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from air_reader.fetcher import fetch, FetchError, validate_url, Article


class TestValidateUrl:
    """Test SSRF protection (review issue #2)."""

    def test_allows_https(self):
        assert validate_url("https://example.com/article") == "https://example.com/article"

    def test_allows_http(self):
        assert validate_url("http://example.com/article") == "http://example.com/article"

    def test_rejects_file_scheme(self):
        with pytest.raises(FetchError, match="scheme"):
            validate_url("file:///etc/passwd")

    def test_rejects_ftp_scheme(self):
        with pytest.raises(FetchError, match="scheme"):
            validate_url("ftp://example.com/file")

    def test_rejects_localhost(self):
        with pytest.raises(FetchError, match="private"):
            validate_url("http://localhost/admin")

    def test_rejects_127_0_0_1(self):
        with pytest.raises(FetchError, match="private"):
            validate_url("http://127.0.0.1/admin")

    def test_rejects_private_10_range(self):
        with pytest.raises(FetchError, match="private"):
            validate_url("http://10.0.0.1/internal")

    def test_rejects_private_172_range(self):
        with pytest.raises(FetchError, match="private"):
            validate_url("http://172.16.0.1/internal")

    def test_rejects_private_192_168_range(self):
        with pytest.raises(FetchError, match="private"):
            validate_url("http://192.168.1.1/internal")

    def test_rejects_metadata_ip(self):
        with pytest.raises(FetchError, match="private"):
            validate_url("http://169.254.169.254/latest/meta-data/")

    def test_rejects_empty_url(self):
        with pytest.raises(FetchError):
            validate_url("")

    def test_rejects_no_host(self):
        with pytest.raises(FetchError):
            validate_url("http://")


class TestFetch:
    @pytest.mark.asyncio
    async def test_returns_cached_article(self, tmp_cache_db):
        from air_reader import cache
        cache.put(url="https://example.com", text="cached text", title="Cached")

        article = await fetch("https://example.com")
        assert article.from_cache is True
        assert article.text == "cached text"

    @pytest.mark.asyncio
    async def test_ssrf_blocked(self):
        with pytest.raises(FetchError, match="private"):
            await fetch("http://169.254.169.254/latest/meta-data/")

    @pytest.mark.asyncio
    async def test_trafilatura_success(self, tmp_cache_db):
        html = "<html><body><p>Article body content here that is long enough.</p></body></html>"
        extracted = "Article body content here that is long enough." + " More." * 50

        with patch("air_reader.fetcher._fetch_trafilatura", return_value=html), \
             patch("air_reader.fetcher._extract", return_value=extracted), \
             patch("air_reader.fetcher._extract_metadata", return_value=None):
            article = await fetch("https://example.com/article")
            assert article.text == extracted
            assert article.from_cache is False
