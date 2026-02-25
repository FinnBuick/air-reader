"""Shared fixtures for AirReader tests."""

from __future__ import annotations

import os
import tempfile

import pytest

# Ensure config module can be imported without real secrets
os.environ.setdefault("WHATSAPP_TOKEN", "test-token")
os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", "123456")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "test-verify")
os.environ.setdefault("WHATSAPP_APP_SECRET", "test-app-secret")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("SEARCH_BACKEND", "google")
os.environ.setdefault("GOOGLE_CSE_KEY", "test-cse-key")
os.environ.setdefault("GOOGLE_CSE_CX", "test-cse-cx")


@pytest.fixture()
def tmp_cache_db(monkeypatch):
    """Provide a temporary SQLite DB path and initialise the cache schema."""
    from air_reader import cache, config

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    monkeypatch.setattr(config, "CACHE_DB_PATH", db_path)
    cache.init_db()
    yield db_path

    os.unlink(db_path)


def _make_whatsapp_payload(*messages: dict) -> dict:
    """Build a minimal WhatsApp webhook payload for testing."""
    msg_list = []
    for m in messages:
        msg_list.append(
            {
                "from": m.get("from", "12125551234"),
                "id": m.get("id", "wamid.test"),
                "type": "text",
                "text": {"body": m.get("text", "help")},
            }
        )
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": msg_list,
                        }
                    }
                ]
            }
        ]
    }
