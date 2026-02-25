"""Tests for air_reader.parser — command parsing."""

from air_reader.parser import Command, ParseResult, parse


class TestHelp:
    def test_help_lower(self):
        r = parse("help")
        assert r.command == Command.HELP
        assert r.payload is None

    def test_help_upper(self):
        r = parse("HELP")
        assert r.command == Command.HELP

    def test_help_with_whitespace(self):
        r = parse("  help  ")
        assert r.command == Command.HELP


class TestFetchFull:
    def test_url_prefix(self):
        r = parse("url: https://example.com/article")
        assert r.command == Command.FETCH_FULL
        assert r.payload == "https://example.com/article"

    def test_read_prefix(self):
        r = parse("read: https://example.com/article")
        assert r.command == Command.FETCH_FULL
        assert r.payload == "https://example.com/article"

    def test_url_prefix_case_insensitive(self):
        r = parse("URL: https://example.com")
        assert r.command == Command.FETCH_FULL

    def test_bare_url(self):
        r = parse("https://example.com/page")
        assert r.command == Command.FETCH_FULL
        assert r.payload == "https://example.com/page"

    def test_bare_url_in_sentence(self):
        r = parse("check out https://example.com/page please")
        assert r.command == Command.FETCH_FULL
        assert r.payload == "https://example.com/page"


class TestSummarize:
    def test_sum_default(self):
        r = parse("sum: https://example.com")
        assert r.command == Command.FETCH_SUMMARIZED
        assert r.payload == "https://example.com"
        assert r.extra == "medium"

    def test_sum_short(self):
        r = parse("sum:short: https://example.com")
        assert r.command == Command.FETCH_SUMMARIZED
        assert r.extra == "short"

    def test_sum_long(self):
        r = parse("sum:long: https://example.com")
        assert r.command == Command.FETCH_SUMMARIZED
        assert r.extra == "long"

    def test_tldr(self):
        r = parse("tl;dr: https://example.com")
        assert r.command == Command.FETCH_SUMMARIZED
        assert r.extra == "short"

    def test_sum_case_insensitive(self):
        r = parse("SUM: https://example.com")
        assert r.command == Command.FETCH_SUMMARIZED


class TestSearch:
    def test_search_basic(self):
        r = parse("search: python asyncio tutorial")
        assert r.command == Command.SEARCH
        assert r.payload == "python asyncio tutorial"

    def test_search_case_insensitive(self):
        r = parse("SEARCH: query")
        assert r.command == Command.SEARCH


class TestUnknown:
    def test_random_text(self):
        r = parse("hello world")
        assert r.command == Command.UNKNOWN
        assert r.payload == "hello world"

    def test_empty_string(self):
        r = parse("")
        assert r.command == Command.UNKNOWN
