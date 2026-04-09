#!/usr/bin/env python3
"""Tests for profile-aware SKILL.md template helpers."""


def test_reference_profile_includes_lookup_language():
    from yonyou_doc2skill.cli.profile_templates import build_profile_sections

    text = build_profile_sections("reference", "react")

    assert "Quick lookup" in text
    assert "API" in text


def test_tutorial_profile_includes_learning_path():
    from yonyou_doc2skill.cli.profile_templates import build_profile_sections

    text = build_profile_sections("tutorial", "react")

    assert "Learning Path" in text
    assert "start" in text.lower()
