"""Tests for air_reader.chunker — article chunking."""

from air_reader import config
from air_reader.chunker import build_chunks, _safe_split


class TestSafeSplit:
    def test_short_text_single_chunk(self):
        result = _safe_split("Hello world.", 100)
        assert result == ["Hello world."]

    def test_splits_on_paragraph_boundary(self):
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        result = _safe_split(text, 30)
        assert len(result) >= 2
        # No chunk should exceed max_chars
        for chunk in result:
            assert len(chunk) <= 30

    def test_splits_on_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence."
        result = _safe_split(text, 35)
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 35

    def test_hard_split_very_long_sentence(self):
        text = "a" * 200
        result = _safe_split(text, 50)
        assert len(result) == 4
        assert all(len(c) <= 50 for c in result)


class TestBuildChunks:
    def test_single_short_article(self):
        chunks = build_chunks("Short article text.")
        assert len(chunks) == 1
        assert "— End of article —" in chunks[0]

    def test_includes_title_in_header(self):
        chunks = build_chunks("Some text.", title="My Title")
        assert "📄 My Title" in chunks[0]

    def test_includes_author_and_date(self):
        chunks = build_chunks("Some text.", author="Alice", date="2025-01-01")
        assert "Alice" in chunks[0]
        assert "2025-01-01" in chunks[0]

    def test_multi_chunk_numbering(self, monkeypatch):
        monkeypatch.setattr(config, "CHUNK_SIZE", 50)
        text = "A" * 200
        chunks = build_chunks(text)
        assert len(chunks) > 1
        # Last chunk has end marker
        assert "— End of article —" in chunks[-1]
        # Second chunk has numbering prefix
        assert chunks[1].startswith("[2/")

    def test_end_marker_on_single_chunk(self):
        chunks = build_chunks("Hello world.")
        assert chunks[0].endswith("— End of article —")
