"""
config.py — Environment variables and constants for AirReader.

Required env vars are validated at startup via ``validate()``, not at import
time, so that modules can be imported in tests without every secret present.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str | None = None) -> str:
    """Return an env var, falling back to *default* (empty string if None)."""
    return os.environ.get(key, default if default is not None else "")


# WhatsApp Cloud API
WHATSAPP_TOKEN: str = _env("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID: str = _env("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN: str = _env("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_APP_SECRET: str = _env("WHATSAPP_APP_SECRET")

WHATSAPP_API_URL: str = ""  # built lazily by validate()

# Anthropic
ANTHROPIC_API_KEY: str = _env("ANTHROPIC_API_KEY")

# Access control — only this phone number can interact with the bot
ALLOWED_SENDER: str = _env("ALLOWED_SENDER")

# Search
SEARCH_BACKEND: str = _env("SEARCH_BACKEND", "google")  # "google" | "searxng"
GOOGLE_CSE_KEY: str = _env("GOOGLE_CSE_KEY")
GOOGLE_CSE_CX: str = _env("GOOGLE_CSE_CX")
SEARXNG_URL: str = _env("SEARXNG_URL", "http://localhost:8888")

# Caching
CACHE_DB_PATH: str = _env("CACHE_DB_PATH", "air_reader_cache.db")
CACHE_TTL_SECONDS: int = int(_env("CACHE_TTL_SECONDS", str(24 * 3600)))  # 24 h

# Content extraction
MIN_CONTENT_LENGTH: int = 200          # below this → trigger Playwright fallback
CHUNK_SIZE: int = 3_000                # target chars per WhatsApp message
PLAYWRIGHT_TIMEOUT_MS: int = 15_000

# Summarisation
SUMMARISE_MODEL: str = "claude-sonnet-4-20250514"
SUMMARISE_MAX_TOKENS: int = 2048

# Required env vars — checked once at startup
_REQUIRED = [
    "WHATSAPP_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_VERIFY_TOKEN",
    "ANTHROPIC_API_KEY",
]


class ConfigError(Exception):
    """Raised when required configuration is missing."""


def validate() -> None:
    """Validate that all required env vars are set. Call once at startup."""
    global WHATSAPP_API_URL

    missing = [k for k in _REQUIRED if not globals().get(k)]
    if missing:
        raise ConfigError(f"Missing required env vars: {', '.join(missing)}")

    WHATSAPP_API_URL = (
        f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
