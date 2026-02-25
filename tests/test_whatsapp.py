"""Tests for air_reader.whatsapp — send/receive helpers."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from air_reader.whatsapp import extract_inbound, send_text, send_chunks


class TestExtractInbound:
    def test_extracts_text_message(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "12125551234",
                                        "id": "wamid.abc",
                                        "type": "text",
                                        "text": {"body": "hello"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        messages = extract_inbound(payload)
        assert len(messages) == 1
        assert messages[0]["from"] == "12125551234"
        assert messages[0]["text"] == "hello"
        assert messages[0]["message_id"] == "wamid.abc"

    def test_ignores_non_text_messages(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "12125551234",
                                        "id": "wamid.abc",
                                        "type": "image",
                                        "image": {"id": "img123"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        messages = extract_inbound(payload)
        assert messages == []

    def test_empty_payload(self):
        assert extract_inbound({}) == []

    def test_status_update_payload(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [{"id": "wamid.abc", "status": "delivered"}]
                            }
                        }
                    ]
                }
            ]
        }
        assert extract_inbound(payload) == []

    def test_multiple_messages(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {"from": "111", "id": "a", "type": "text", "text": {"body": "m1"}},
                                    {"from": "222", "id": "b", "type": "text", "text": {"body": "m2"}},
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        messages = extract_inbound(payload)
        assert len(messages) == 2


class TestSendText:
    @pytest.mark.asyncio
    async def test_send_text_posts_correctly(self):
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("air_reader.whatsapp.httpx.AsyncClient", return_value=mock_client):
            await send_text("12125551234", "Hello")

        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["to"] == "12125551234"
        assert payload["text"]["body"] == "Hello"


class TestSendChunks:
    @pytest.mark.asyncio
    async def test_sends_all_chunks_in_order(self):
        sent = []

        async def mock_send(to, text):
            sent.append(text)

        with patch("air_reader.whatsapp.send_text", side_effect=mock_send):
            await send_chunks("123", ["chunk1", "chunk2", "chunk3"])

        assert sent == ["chunk1", "chunk2", "chunk3"]
