"""Tests for air_reader.main — webhook signature verification & dispatch."""

import hashlib
import hmac
import json

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from air_reader import config


def _sign_payload(body: bytes, secret: str) -> str:
    """Compute the X-Hub-Signature-256 header value."""
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


@pytest.fixture()
def client(monkeypatch, tmp_cache_db):
    """Create a TestClient with config validated."""
    monkeypatch.setattr(config, "WHATSAPP_TOKEN", "test-token")
    monkeypatch.setattr(config, "WHATSAPP_PHONE_NUMBER_ID", "123456")
    monkeypatch.setattr(config, "WHATSAPP_VERIFY_TOKEN", "test-verify")
    monkeypatch.setattr(config, "WHATSAPP_APP_SECRET", "test-secret")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(config, "ALLOWED_SENDER", "")
    config.validate()

    from air_reader.main import app
    return TestClient(app)


class TestWebhookVerification:
    def test_valid_verification(self, client):
        resp = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify",
                "hub.challenge": "challenge_abc",
            },
        )
        assert resp.status_code == 200
        assert resp.text == "challenge_abc"

    def test_invalid_token_returns_403(self, client):
        resp = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "challenge",
            },
        )
        assert resp.status_code == 403


class TestWebhookSignature:
    """Test that POST /webhook validates X-Hub-Signature-256 (review issue #1)."""

    def test_missing_signature_returns_403(self, client):
        payload = {"entry": []}
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 403

    def test_invalid_signature_returns_403(self, client):
        payload = {"entry": []}
        resp = client.post(
            "/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=invalid"},
        )
        assert resp.status_code == 403

    def test_valid_signature_accepted(self, client):
        payload = {"entry": []}
        body = json.dumps(payload).encode()
        sig = _sign_payload(body, "test-secret")

        with patch("air_reader.main.whatsapp") as mock_wa:
            mock_wa.extract_inbound.return_value = []
            resp = client.post(
                "/webhook",
                content=body,
                headers={
                    "X-Hub-Signature-256": sig,
                    "Content-Type": "application/json",
                },
            )
        assert resp.status_code == 200


class TestDispatch:
    def _post_message(self, client, text, sender="12125551234"):
        payload_dict = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": sender,
                                        "id": "wamid.test",
                                        "type": "text",
                                        "text": {"body": text},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        body = json.dumps(payload_dict).encode()
        sig = _sign_payload(body, "test-secret")
        return client.post(
            "/webhook",
            content=body,
            headers={
                "X-Hub-Signature-256": sig,
                "Content-Type": "application/json",
            },
        )

    def test_help_command(self, client):
        with patch("air_reader.main.whatsapp") as mock_wa:
            mock_wa.extract_inbound.side_effect = lambda p: __import__(
                "air_reader.whatsapp", fromlist=["extract_inbound"]
            ).extract_inbound(p)
            mock_wa.send_text = AsyncMock()
            resp = self._post_message(client, "help")

        assert resp.status_code == 200
        mock_wa.send_text.assert_called()
        sent_text = mock_wa.send_text.call_args[0][1]
        assert "AirReader commands" in sent_text

    def test_blocked_sender(self, client, monkeypatch):
        monkeypatch.setattr(config, "ALLOWED_SENDER", "99999")

        with patch("air_reader.main.whatsapp") as mock_wa:
            mock_wa.extract_inbound.side_effect = lambda p: __import__(
                "air_reader.whatsapp", fromlist=["extract_inbound"]
            ).extract_inbound(p)
            mock_wa.send_text = AsyncMock()
            resp = self._post_message(client, "help", sender="12125551234")

        assert resp.status_code == 200
        mock_wa.send_text.assert_not_called()
