"""Tests for content sources and scraping (HTTP fully stubbed)."""

from __future__ import annotations

import pytest

from post_it.exceptions import SourceError
from post_it.sources.ai_direct import AiDirectSource
from post_it.sources.scraping import fetch_and_extract, make_client
from post_it.sources.url_file import UrlFileSource

_HTML = """
<html><head><title>Test Page</title></head>
<body><article><p>This is the main body content of the article that should be
extracted as the primary text for the post generator to use.</p></article></body>
</html>
"""


def test_fetch_and_extract_success(httpx_mock):
    httpx_mock.add_response(url="https://example.com/a", text=_HTML)
    with make_client() as client:
        result = fetch_and_extract("https://example.com/a", client=client)
    assert result.ok
    assert "main body content" in result.text


def test_fetch_and_extract_http_error_does_not_raise(httpx_mock):
    httpx_mock.add_response(url="https://example.com/missing", status_code=404)
    with make_client() as client:
        result = fetch_and_extract("https://example.com/missing", client=client)
    assert not result.ok
    assert result.error is not None


def test_url_file_source(tmp_path, httpx_mock):
    httpx_mock.add_response(url="https://example.com/a", text=_HTML)
    urls = tmp_path / "urls.txt"
    urls.write_text("# a comment\nhttps://example.com/a\n\n", encoding="utf-8")

    result = UrlFileSource().collect(str(urls))
    assert result.kind == "url_file"
    assert "main body content" in result.combined_text


def test_url_file_all_failed_raises(tmp_path, httpx_mock):
    httpx_mock.add_response(url="https://example.com/x", status_code=500)
    urls = tmp_path / "urls.txt"
    urls.write_text("https://example.com/x\n", encoding="utf-8")
    with pytest.raises(SourceError):
        UrlFileSource().collect(str(urls))


def test_url_file_missing_file():
    with pytest.raises(SourceError):
        UrlFileSource().collect("/nope/urls.txt")


def test_ai_direct_topic():
    result = AiDirectSource().collect("the future of RAG")
    assert result.kind == "ai_direct_topic"
    assert result.topic == "the future of RAG"
    assert result.combined_text == "the future of RAG"


def test_ai_direct_link(httpx_mock):
    httpx_mock.add_response(url="https://example.com/a", text=_HTML)
    result = AiDirectSource().collect("https://example.com/a")
    assert result.kind == "ai_direct_link"
    assert "main body content" in result.combined_text


def test_ai_direct_empty_raises():
    with pytest.raises(SourceError):
        AiDirectSource().collect("   ")
