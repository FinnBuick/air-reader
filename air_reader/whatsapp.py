"""
whatsapp.py — WhatsApp Cloud API send/receive helpers.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from air_reader import config

logger = logging.getLogger(__name__)

_HEADERS = {
    "Authorization": f"Bearer {config.WHATSAPP_TOKEN}",
    "Content-Type": "application/json",
}


async def send_text(to: str, text: str) -> None:
    """Send a single text message to a WhatsApp number."""
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(config.WHATSAPP_API_URL, json=payload, headers=_HEADERS)
        if resp.status_code != 200:
            logger.error(
                "WhatsApp send failed: %s %s", resp.status_code, resp.text
            )
            resp.raise_for_status()


async def send_chunks(to: str, chunks: list[str]) -> None:
    """Send a list of text chunks sequentially to preserve reading order."""
    for chunk in chunks:
        await send_text(to, chunk)


def extract_inbound(payload: dict[str, Any]) -> list[dict[str, str]]:
    """
    Extract inbound messages from a WhatsApp webhook POST payload.

    Returns a list of dicts with keys: 'from', 'text', 'message_id'.
    Returns an empty list for non-message events (status updates, etc.).
    """
    messages = []
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    if msg.get("type") != "text":
                        continue
                    messages.append(
                        {
                            "from": msg["from"],
                            "text": msg["text"]["body"],
                            "message_id": msg["id"],
                        }
                    )
    except (KeyError, TypeError) as exc:
        logger.warning("Failed to parse inbound payload: %s", exc)
    return messages
