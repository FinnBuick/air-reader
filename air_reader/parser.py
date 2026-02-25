"""
parser.py — Incoming WhatsApp message command parser.

Parses raw message text into a (Command, payload) tuple.
"""

from __future__ import annotations

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

# Matches http(s):// URLs anywhere in a string
_URL_RE = re.compile(r"https?://[^\s]+")

# Prefixes for sum: with optional length modifier, e.g. "sum:", "sum:short", "sum:long"
_SUM_RE = re.compile(r"^sum(?::(?P<length>short|medium|long))?:\s*", re.IGNORECASE)


class Command(Enum):
    FETCH_FULL = auto()        # url: / read:
    FETCH_SUMMARIZED = auto()  # sum:
    SEARCH = auto()            # search:
    HELP = auto()              # help
    UNKNOWN = auto()


@dataclass
class ParseResult:
    command: Command
    payload: Optional[str]              # URL, query string, or None
    extra: Optional[str] = None         # e.g. summary length ("short", "medium", "long")


def parse(message: str) -> ParseResult:
    """Parse raw WhatsApp message text into a ParseResult."""
    text = message.strip()

    # help
    if text.lower() == "help":
        return ParseResult(command=Command.HELP, payload=None)

    # url: / read:
    if re.match(r"^(url|read):\s*", text, re.IGNORECASE):
        url = re.split(r"^(url|read):\s*", text, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
        return ParseResult(command=Command.FETCH_FULL, payload=url)

    # sum: / sum:short / sum:medium / sum:long
    m = _SUM_RE.match(text)
    if m:
        length = m.group("length") or "medium"
        url = text[m.end():].strip()
        return ParseResult(command=Command.FETCH_SUMMARIZED, payload=url, extra=length)

    # search:
    if re.match(r"^search:\s*", text, re.IGNORECASE):
        query = re.split(r"^search:\s*", text, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
        return ParseResult(command=Command.SEARCH, payload=query)

    # tl;dr: alias for sum:
    if re.match(r"^tl;dr:\s*", text, re.IGNORECASE):
        url = re.split(r"^tl;dr:\s*", text, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
        return ParseResult(command=Command.FETCH_SUMMARIZED, payload=url, extra="short")

    # bare URL — default to full extraction
    m_url = _URL_RE.search(text)
    if m_url:
        return ParseResult(command=Command.FETCH_FULL, payload=m_url.group())

    return ParseResult(command=Command.UNKNOWN, payload=text)
