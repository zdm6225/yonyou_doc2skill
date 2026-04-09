#!/usr/bin/env python3
"""Tests for Confluence API auth mode resolution."""

from yonyou_doc2skill.cli.confluence_scraper import ConfluenceToSkillConverter


def _make_converter(**overrides):
    config = {
        "name": "test-wiki",
        "base_url": "https://wiki.example.com",
        "space_key": "DEV",
        "description": "Test wiki",
        "max_pages": 5,
    }
    config.update(overrides)
    return ConfluenceToSkillConverter(config)


def test_build_auth_candidates_supports_cookie_basic_and_bearer(monkeypatch):
    monkeypatch.delenv("CONFLUENCE_COOKIE", raising=False)
    monkeypatch.delenv("ATLASSIAN_COOKIE", raising=False)
    monkeypatch.delenv("CONFLUENCE_USERNAME", raising=False)
    monkeypatch.delenv("ATLASSIAN_USERNAME", raising=False)
    monkeypatch.delenv("CONFLUENCE_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_TOKEN", raising=False)

    converter = _make_converter(
        cookie="JSESSIONID=abc",
        username="alice@example.com",
        token="secret-token",
    )

    candidates = converter._build_auth_candidates()

    assert [candidate["mode"] for candidate in candidates] == ["cookie", "basic", "bearer"]


def test_build_auth_candidates_supports_bearer_without_username(monkeypatch):
    monkeypatch.delenv("CONFLUENCE_COOKIE", raising=False)
    monkeypatch.delenv("ATLASSIAN_COOKIE", raising=False)
    monkeypatch.delenv("CONFLUENCE_USERNAME", raising=False)
    monkeypatch.delenv("ATLASSIAN_USERNAME", raising=False)
    monkeypatch.delenv("CONFLUENCE_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_TOKEN", raising=False)

    converter = _make_converter(token="secret-token")

    candidates = converter._build_auth_candidates()

    assert [candidate["mode"] for candidate in candidates] == ["bearer"]


def test_build_auth_candidates_supports_cookie_from_env(monkeypatch):
    monkeypatch.setenv("CONFLUENCE_COOKIE", "JSESSIONID=abc")
    monkeypatch.delenv("ATLASSIAN_COOKIE", raising=False)
    monkeypatch.delenv("CONFLUENCE_USERNAME", raising=False)
    monkeypatch.delenv("ATLASSIAN_USERNAME", raising=False)
    monkeypatch.delenv("CONFLUENCE_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_TOKEN", raising=False)

    converter = _make_converter()

    candidates = converter._build_auth_candidates()

    assert [candidate["mode"] for candidate in candidates] == ["cookie"]
