"""Tests for air_reader.search — web search and result formatting."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from air_reader.search import (
    SearchResult,
    format_results,
    search,
    _domain,
)


class TestFormatResults:
    def test_no_results(self):
        text = format_results("python", [])
        assert "No results found" in text
        assert "python" in text

    def test_formats_results(self):
        results = [
            SearchResult(rank=1, title="Python Docs", url="https://python.org", snippet="Official"),
            SearchResult(rank=2, title="Tutorial", url="https://tutorial.com", snippet=None),
        ]
        text = format_results("python", results)
        assert "Python Docs" in text
        assert "https://python.org" in text
        assert "Tutorial" in text
        assert "Reply with a URL" in text

    def test_includes_domain(self):
        results = [
            SearchResult(rank=1, title="Test", url="https://example.com/page", snippet="snip"),
        ]
        text = format_results("test", results)
        assert "example.com" in text


class TestDomain:
    def test_extracts_domain(self):
        assert _domain("https://example.com/path") == "example.com"

    def test_empty_on_bad_url(self):
        assert _domain("not-a-url") == ""


class TestGoogleSearch:
    @pytest.mark.asyncio
    async def test_google_search_parses_response(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {"title": "Result 1", "link": "https://example.com/1", "snippet": "Snippet 1"},
                {"title": "Result 2", "link": "https://example.com/2", "snippet": "Snippet 2"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("air_reader.search.httpx.AsyncClient", return_value=mock_client):
            results = await search("test query")

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[1].url == "https://example.com/2"


class TestSearxngSearch:
    @pytest.mark.asyncio
    async def test_searxng_search_parses_response(self, monkeypatch):
        from air_reader import config
        monkeypatch.setattr(config, "SEARCH_BACKEND", "searxng")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"title": "SearX Result", "url": "https://example.com/s", "content": "Snippet"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("air_reader.search.httpx.AsyncClient", return_value=mock_client):
            results = await search("test")

        assert len(results) == 1
        assert results[0].title == "SearX Result"


class TestUnknownBackend:
    @pytest.mark.asyncio
    async def test_unknown_backend_raises(self, monkeypatch):
        from air_reader import config
        monkeypatch.setattr(config, "SEARCH_BACKEND", "bing")

        with pytest.raises(RuntimeError, match="Unknown SEARCH_BACKEND"):
            await search("test")
