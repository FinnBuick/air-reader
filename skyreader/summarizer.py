"""
summarizer.py — Claude API summarization (invoked only for `sum:` commands).
"""

from __future__ import annotations

from typing import Optional

import anthropic

from skyreader import config

_LENGTH_GUIDANCE = {
    "short": "3-5 sentences",
    "medium": "2-3 paragraphs",
    "long": "roughly half the original length",
}

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def summarize(
    text: str,
    title: Optional[str] = None,
    length: str = "medium",
) -> str:
    """
    Summarize *text* using the Claude API.

    Args:
        text:   The article body to summarize.
        title:  Optional article title for context.
        length: One of "short", "medium", "long".

    Returns:
        The summary as a plain string.
    """
    if length not in _LENGTH_GUIDANCE:
        length = "medium"

    title_line = f"Title: {title}\n\n" if title else ""
    guidance = _LENGTH_GUIDANCE[length]

    prompt = (
        f"Summarize the following article. Provide a {guidance} summary that "
        f"captures the key points, arguments, and conclusions.\n\n"
        f"{title_line}"
        f"Article:\n{text}"
    )

    client = _get_client()
    response = client.messages.create(
        model=config.SUMMARISE_MODEL,
        max_tokens=config.SUMMARISE_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
