"""Tests for air_reader.summarizer — async Claude API summarization."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from air_reader.summarizer import summarize


class TestSummarize:
    @pytest.mark.asyncio
    async def test_summarize_returns_text(self):
        """summarize() should be async and return the model's text."""
        mock_content = MagicMock()
        mock_content.text = "This is the summary."

        mock_response = MagicMock()
        mock_response.content = [mock_content]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("air_reader.summarizer._get_client", return_value=mock_client):
            result = await summarize(text="Long article text...", title="My Article")

        assert result == "This is the summary."

    @pytest.mark.asyncio
    async def test_summarize_uses_correct_length(self):
        mock_content = MagicMock()
        mock_content.text = "Short summary."

        mock_response = MagicMock()
        mock_response.content = [mock_content]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("air_reader.summarizer._get_client", return_value=mock_client):
            await summarize(text="Text", length="short")

        call_args = mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "3-5 sentences" in prompt

    @pytest.mark.asyncio
    async def test_summarize_invalid_length_defaults_medium(self):
        mock_content = MagicMock()
        mock_content.text = "Medium summary."

        mock_response = MagicMock()
        mock_response.content = [mock_content]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("air_reader.summarizer._get_client", return_value=mock_client):
            await summarize(text="Text", length="invalid")

        call_args = mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "2-3 paragraphs" in prompt
