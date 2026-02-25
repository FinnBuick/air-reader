"""
main.py — FastAPI application: WhatsApp webhook endpoint and request dispatcher.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from skyreader import cache, config, whatsapp
from skyreader.chunker import build_chunks
from skyreader.fetcher import Article, FetchError, fetch
from skyreader.parser import Command, parse
from skyreader.search import format_results, search
from skyreader.summarizer import summarize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

HELP_TEXT = """📖 SkyReader commands:

url: <link>     — Fetch full article
read: <link>    — Alias for url:
sum: <link>     — Summarize article (medium length)
sum:short: <link> — Short summary (3-5 sentences)
sum:long: <link>  — Long summary (~half the article)
tl;dr: <link>   — Quick 3-5 sentence summary
search: <query> — Web search, top 5 results
help            — Show this message

Tip: You can also paste a bare URL and I'll fetch it automatically."""


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.init_db()
    logger.info("SkyReader started. Cache DB: %s", config.CACHE_DB_PATH)
    yield
    logger.info("SkyReader shutting down.")


app = FastAPI(title="SkyReader", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Webhook verification (GET) — Meta sends a challenge token on initial setup
# ---------------------------------------------------------------------------

@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    if hub_mode == "subscribe" and hub_verify_token == config.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified by Meta.")
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Forbidden")


# ---------------------------------------------------------------------------
# Inbound messages (POST)
# ---------------------------------------------------------------------------

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload: dict[str, Any] = await request.json()
    messages = whatsapp.extract_inbound(payload)

    for msg in messages:
        sender = msg["from"]
        text = msg["text"]

        # Access control
        if config.ALLOWED_SENDER and sender != config.ALLOWED_SENDER:
            logger.warning("Blocked message from unauthorized sender: %s", sender)
            continue

        logger.info("Message from %s: %s", sender, text[:120])
        await _dispatch(sender, text)

    # Always return 200 — Meta will retry on non-200 responses
    return {"status": "ok"}


async def _dispatch(sender: str, text: str) -> None:
    """Parse the incoming message and route to the appropriate handler."""
    result = parse(text)

    try:
        if result.command == Command.HELP:
            await whatsapp.send_text(sender, HELP_TEXT)

        elif result.command == Command.FETCH_FULL:
            await _handle_fetch(sender, result.payload, summarize_length=None)

        elif result.command == Command.FETCH_SUMMARIZED:
            await _handle_fetch(
                sender, result.payload, summarize_length=result.extra or "medium"
            )

        elif result.command == Command.SEARCH:
            await _handle_search(sender, result.payload)

        else:  # UNKNOWN
            await whatsapp.send_text(
                sender,
                "🤔 Didn't understand that. Send `help` for available commands.",
            )

    except FetchError as exc:
        logger.warning("FetchError for %s: %s", sender, exc)
        await whatsapp.send_text(sender, f"❌ {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error handling message from %s", sender)
        await whatsapp.send_text(
            sender,
            "❌ Something went wrong on my end. Please try again.",
        )


async def _handle_fetch(
    sender: str,
    url: str | None,
    summarize_length: str | None,
) -> None:
    if not url:
        await whatsapp.send_text(sender, "❌ Please provide a URL after the command.")
        return

    await whatsapp.send_text(sender, "⏳ Fetching article…")

    article: Article = await fetch(url)

    if not article.text:
        raise FetchError(f"No content extracted from {url}")

    if summarize_length:
        # Summarization path
        await whatsapp.send_text(sender, "✍️ Summarizing…")
        summary = summarize(
            text=article.text,
            title=article.title,
            length=summarize_length,
        )
        header_parts = []
        if article.title:
            header_parts.append(f"📄 {article.title}")
        if article.author or article.date:
            meta = " · ".join(filter(None, [article.author, article.date]))
            header_parts.append(f"✍️ {meta}")
        header_parts.append(f"🔖 Summary ({summarize_length}):\n")
        header = "\n".join(header_parts) + "\n"
        await whatsapp.send_text(sender, header + summary)
    else:
        # Full article path
        num_chars = len(article.text)
        if num_chars > 10_000:
            estimated_chunks = num_chars // 3_000 + 1
            await whatsapp.send_text(
                sender,
                f"📄 Long article — sending in ~{estimated_chunks} parts…",
            )
        chunks = build_chunks(
            text=article.text,
            title=article.title,
            author=article.author,
            date=article.date,
        )
        await whatsapp.send_chunks(sender, chunks)


async def _handle_search(sender: str, query: str | None) -> None:
    if not query:
        await whatsapp.send_text(sender, "❌ Please provide a search query after `search:`.")
        return

    await whatsapp.send_text(sender, f"🔍 Searching for "{query}"…")
    results = await search(query)
    await whatsapp.send_text(sender, format_results(query, results))
