"""
chunker.py — Splits long article text into WhatsApp-friendly chunks.

Rules:
  - Target chunk size: CHUNK_SIZE characters (default 3,000)
  - Never break mid-sentence
  - Never break mid-paragraph if the paragraph fits in remaining space
  - First chunk includes article metadata header
  - Subsequent chunks prefixed with "[N/total] ..."
  - Final chunk appended with "— End of article —"
"""

from __future__ import annotations

import re
from typing import Optional

from air_reader import config

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_into_sentences(text: str) -> list[str]:
    """Split text at sentence boundaries, preserving the trailing space."""
    parts = _SENTENCE_END.split(text)
    return parts


def _safe_split(text: str, max_chars: int) -> list[str]:
    """
    Split *text* into chunks of at most *max_chars*, breaking on sentence
    boundaries where possible, paragraph boundaries otherwise.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    paragraphs = text.split("\n\n")
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Paragraph fits in current chunk
        candidate = (current + "\n\n" + para).lstrip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue

        # Paragraph is too large to fit even alone — split by sentence
        if len(para) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            sentences = _split_into_sentences(para)
            for sentence in sentences:
                trial = (current + " " + sentence).lstrip() if current else sentence
                if len(trial) <= max_chars:
                    current = trial
                else:
                    if current:
                        chunks.append(current.strip())
                    # Single sentence longer than max_chars → hard-split
                    while len(sentence) > max_chars:
                        chunks.append(sentence[:max_chars])
                        sentence = sentence[max_chars:]
                    current = sentence
            continue

        # Paragraph fits alone but not in current chunk → flush current first
        if current:
            chunks.append(current.strip())
        current = para

    if current:
        chunks.append(current.strip())

    return chunks


def build_chunks(
    text: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    date: Optional[str] = None,
) -> list[str]:
    """
    Return a list of WhatsApp message strings for an article.

    The first chunk carries a metadata header; all chunks are numbered when
    there is more than one.
    """
    # Build metadata header for the first chunk
    header_lines: list[str] = []
    if title:
        header_lines.append(f"📄 {title}")
    meta_parts: list[str] = []
    if author:
        meta_parts.append(author)
    if date:
        meta_parts.append(date)
    if meta_parts:
        header_lines.append("✍️ " + " · ".join(meta_parts))

    header = "\n".join(header_lines) + "\n\n" if header_lines else ""

    # Reserve space for header in first chunk
    first_max = config.CHUNK_SIZE - len(header)
    if first_max < 200:
        # Header is very long; just prepend it to the first chunk even if it
        # pushes slightly over the target
        first_max = config.CHUNK_SIZE

    # Split the body
    body_chunks = _safe_split(text, config.CHUNK_SIZE)

    # If header fits alongside the first body chunk, merge them
    if body_chunks and len(header) + len(body_chunks[0]) <= config.CHUNK_SIZE + 50:
        body_chunks[0] = header + body_chunks[0]
    elif header:
        body_chunks.insert(0, header.strip())

    total = len(body_chunks)

    if total == 1:
        return [body_chunks[0] + "\n\n— End of article —"]

    # Number multi-chunk articles
    result: list[str] = []
    for i, chunk in enumerate(body_chunks, start=1):
        prefix = f"[{i}/{total}]\n\n" if i > 1 else ""
        suffix = "\n\n— End of article —" if i == total else ""
        result.append(prefix + chunk + suffix)

    return result
