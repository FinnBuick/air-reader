"""
config.py — Environment variables and constants for AirReader.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# WhatsApp Cloud API
WHATSAPP_TOKEN: str = os.environ["WHATSAPP_TOKEN"]
WHATSAPP_PHONE_NUMBER_ID: str = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
WHATSAPP_VERIFY_TOKEN: str = os.environ["WHATSAPP_VERIFY_TOKEN"]

WHATSAPP_API_URL = (
    f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
)

# Anthropic
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]

# Access control — only this phone number can interact with the bot
ALLOWED_SENDER: str = os.environ.get("ALLOWED_SENDER", "")

# Search
SEARCH_BACKEND: str = os.environ.get("SEARCH_BACKEND", "google")  # "google" | "searxng"
GOOGLE_CSE_KEY: str = os.environ.get("GOOGLE_CSE_KEY", "")
GOOGLE_CSE_CX: str = os.environ.get("GOOGLE_CSE_CX", "")
SEARXNG_URL: str = os.environ.get("SEARXNG_URL", "http://localhost:8888")

# Caching
CACHE_DB_PATH: str = os.environ.get("CACHE_DB_PATH", "air_reader_cache.db")
CACHE_TTL_SECONDS: int = int(os.environ.get("CACHE_TTL_SECONDS", str(24 * 3600)))  # 24 h

# Content extraction
MIN_CONTENT_LENGTH: int = 200          # below this → trigger Playwright fallback
CHUNK_SIZE: int = 3_000                # target chars per WhatsApp message
PLAYWRIGHT_TIMEOUT_MS: int = 15_000

# Summarisation
SUMMARISE_MODEL: str = "claude-sonnet-4-20250514"
SUMMARISE_MAX_TOKENS: int = 2048
