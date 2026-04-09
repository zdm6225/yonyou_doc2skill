#!/usr/bin/env python3
"""
Tests for public source type integration points.

Covers source detection, config validation, generic merge, CLI wiring,
and source validation for the retained public source types.
"""

import os
from argparse import Namespace
import textwrap

import pytest

from yonyou_doc2skill.cli.config_validator import ConfigValidator
from yonyou_doc2skill.cli.create_command import CreateCommand
from yonyou_doc2skill.cli.execution_context import ExecutionContext
from yonyou_doc2skill.cli.source_detector import SourceDetector, SourceInfo
from yonyou_doc2skill.cli.unified_skill_builder import UnifiedSkillBuilder


# ---------------------------------------------------------------------------
# 1. SourceDetector — new type detection
# ---------------------------------------------------------------------------


class TestSourceDetectorNewTypes:
    """Test that SourceDetector.detect() maps new extensions to correct types."""

    # -- HTML --
    def test_detect_html_extension(self):
        """Test .html → html detection."""
        info = SourceDetector.detect("page.html")
        assert info.type == "html"
        assert info.parsed["file_path"] == "page.html"

    def test_detect_htm_extension(self):
        """Test .htm → html detection."""
        info = SourceDetector.detect("index.HTM")
        assert info.type == "html"
        assert info.parsed["file_path"] == "index.HTM"

    # -- PowerPoint --
    def test_detect_pptx(self):
        """Test .pptx → pptx detection."""
        info = SourceDetector.detect("slides.pptx")
        assert info.type == "pptx"
        assert info.parsed["file_path"] == "slides.pptx"
        assert info.suggested_name == "slides"

    # -- AsciiDoc --
    def test_detect_adoc(self):
        """Test .adoc → asciidoc detection."""
        info = SourceDetector.detect("manual.adoc")
        assert info.type == "asciidoc"
        assert info.parsed["file_path"] == "manual.adoc"

    def test_detect_asciidoc_extension(self):
        """Test .asciidoc → asciidoc detection."""
        info = SourceDetector.detect("guide.ASCIIDOC")
        assert info.type == "asciidoc"
        assert info.parsed["file_path"] == "guide.ASCIIDOC"

    # -- Retired public file types --
    @pytest.mark.parametrize(
        "source",
        [
            "analysis.ipynb",
            "curl.man",
            "git.1",
            "feed.rss",
            "updates.atom",
        ],
    )
    def test_retired_file_types_raise_value_error(self, source):
        """Retired file types should no longer be auto-detected."""
        with pytest.raises(ValueError, match="Cannot determine source type"):
            SourceDetector.detect(source)

    def test_yaml_falls_through_without_openapi_classification(self, tmp_path):
        """Plain YAML should not be classified as openapi."""
        spec = tmp_path / "config.yaml"
        spec.write_text(
            textwrap.dedent(
                """\
                name: demo
                version: 1
                """
            )
        )

        with pytest.raises(ValueError, match="Cannot determine source type"):
            SourceDetector.detect(str(spec))

    def test_openapi_like_yaml_falls_through_without_openapi_classification(self, tmp_path):
        """OpenAPI-looking YAML should also fall through normally."""
        spec = tmp_path / "petstore.yaml"
        spec.write_text(
            textwrap.dedent(
                """\
                openapi: "3.0.0"
                info:
                  title: Petstore
                  version: "1.0.0"
                paths: {}
                """
            )
        )

        with pytest.raises(ValueError, match="Cannot determine source type"):
            SourceDetector.detect(str(spec))

    def test_looks_like_openapi_returns_false_for_missing_file(self):
        """Test _looks_like_openapi returns False for non-existent file."""
        assert SourceDetector._looks_like_openapi("/nonexistent/spec.yaml") is False

    def test_looks_like_openapi_json_key_format(self, tmp_path):
        """Test _looks_like_openapi detects JSON-style keys (quoted)."""
        spec = tmp_path / "api.yaml"
        spec.write_text('"openapi": "3.0.0"\n')
        assert SourceDetector._looks_like_openapi(str(spec)) is True


# ---------------------------------------------------------------------------
# 2. ConfigValidator — new source type validation
# ---------------------------------------------------------------------------


class TestConfigValidatorNewTypes:
    """Test ConfigValidator VALID_SOURCE_TYPES and per-type validation."""

    # Public retained types
    EXPECTED_TYPES = {
        "documentation",
        "github",
        "pdf",
        "local",
        "word",
        "video",
        "html",
        "asciidoc",
        "pptx",
        "confluence",
        "chat",
    }

    def test_public_types_still_allowed(self):
        """Test that retained public types remain in the validator allowlist."""
        assert self.EXPECTED_TYPES.issubset(ConfigValidator.VALID_SOURCE_TYPES)

    def test_removed_public_types_not_in_validator_allowlist(self):
        """Test that retired public types are no longer accepted in configs."""
        removed = {"epub", "jupyter", "openapi", "rss", "manpage", "notion"}
        assert removed.isdisjoint(ConfigValidator.VALID_SOURCE_TYPES)

    @pytest.mark.parametrize(
        "source_type, source_payload",
        [
            ("epub", {"type": "epub", "path": "book.epub"}),
            ("jupyter", {"type": "jupyter", "path": "nb.ipynb"}),
            ("openapi", {"type": "openapi", "path": "spec.yaml"}),
            ("rss", {"type": "rss", "url": "https://example.com/feed.xml"}),
            ("manpage", {"type": "manpage", "path": "git.1"}),
            ("notion", {"type": "notion", "page_id": "page123"}),
        ],
    )
    def test_retired_public_types_rejected_in_config_validation(
        self, source_type, source_payload
    ):
        """Test that retired types are rejected from public config JSON."""
        config = {
            "name": "test",
            "description": "test",
            "sources": [source_payload],
        }
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match=f"Invalid type '{source_type}'"):
            validator.validate()

    def test_unknown_type_rejected(self):
        """Test that an unknown source type is rejected during validation."""
        config = {
            "name": "test",
            "description": "test",
            "sources": [{"type": "foobar"}],
        }
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Invalid type 'foobar'"):
            validator.validate()

    # --- Per-type required-field validation ---

    def _make_config(self, source: dict) -> dict:
        """Helper: wrap a source dict in a valid config structure."""
        return {
            "name": "test",
            "description": "test",
            "sources": [source],
        }

    def test_html_requires_path(self):
        """Test html source validation requires 'path'."""
        config = self._make_config({"type": "html"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'"):
            validator.validate()

    def test_pptx_requires_path(self):
        """Test pptx source validation requires 'path'."""
        config = self._make_config({"type": "pptx"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'"):
            validator.validate()

    def test_asciidoc_requires_path(self):
        """Test asciidoc source validation requires 'path'."""
        config = self._make_config({"type": "asciidoc"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'"):
            validator.validate()

    def test_confluence_requires_url_or_path(self):
        """Test confluence requires 'url'/'base_url' or 'path'."""
        config = self._make_config({"type": "confluence"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field"):
            validator.validate()

    def test_confluence_accepts_base_url(self):
        """Test confluence passes with base_url + space_key."""
        config = self._make_config(
            {
                "type": "confluence",
                "base_url": "https://wiki.example.com",
                "space_key": "DEV",
            }
        )
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_confluence_accepts_path(self):
        """Test confluence passes with export path."""
        config = self._make_config({"type": "confluence", "path": "/exports/wiki"})
        validator = ConfigValidator(config)
        assert validator.validate() is True


    def test_chat_requires_path_or_token(self):
        """Test chat source validation requires 'path' or 'token'."""
        config = self._make_config({"type": "chat"})
        validator = ConfigValidator(config)
        with pytest.raises(ValueError, match="Missing required field 'path'.*or 'token'"):
            validator.validate()

    def test_chat_accepts_path(self):
        """Test chat passes with export path."""
        config = self._make_config({"type": "chat", "path": "/exports/slack"})
        validator = ConfigValidator(config)
        assert validator.validate() is True

    def test_chat_accepts_token_with_channel(self):
        """Test chat passes with API token + channel."""
        config = self._make_config(
            {
                "type": "chat",
                "token": "xoxb-fake",
                "channel": "#general",
            }
        )
        validator = ConfigValidator(config)
        assert validator.validate() is True


# ---------------------------------------------------------------------------
# 3. UnifiedSkillBuilder — generic merge system
# ---------------------------------------------------------------------------


class TestUnifiedSkillBuilderGenericMerge:
    """Test _generic_merge, _append_extra_sources, and _SOURCE_LABELS."""

    def _make_builder(self, tmp_path) -> UnifiedSkillBuilder:
        """Create a minimal builder instance for testing."""
        config = {
            "name": "test_project",
            "description": "A test project for merge testing",
            "sources": [
                {"type": "jupyter", "path": "nb.ipynb"},
                {"type": "rss", "url": "https://example.com/feed.rss"},
            ],
        }
        scraped_data: dict = {}
        builder = UnifiedSkillBuilder(
            config=config,
            scraped_data=scraped_data,
            cache_dir=str(tmp_path / "cache"),
        )
        # Override skill_dir to use tmp_path
        builder.skill_dir = str(tmp_path / "output" / "test_project")
        os.makedirs(builder.skill_dir, exist_ok=True)
        os.makedirs(os.path.join(builder.skill_dir, "references"), exist_ok=True)
        return builder

    def test_generic_merge_produces_valid_markdown(self, tmp_path):
        """Test _generic_merge with two source types produces markdown."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "jupyter": "## When to Use\n\nFor data analysis.\n\n## Quick Reference\n\nImport pandas.",
            "rss": "## When to Use\n\nFor feed monitoring.\n\n## Feed Items\n\nLatest entries.",
        }
        result = builder._generic_merge(skill_mds)

        # Must be non-empty markdown
        assert len(result) > 100
        # Must contain the project title
        assert "Test Project" in result

    def test_generic_merge_includes_yaml_frontmatter(self, tmp_path):
        """Test _generic_merge includes YAML frontmatter."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "html": "## Overview\n\nHTML content here.",
        }
        result = builder._generic_merge(skill_mds)

        assert result.startswith("---\n")
        assert "name: test-project" in result
        assert "description: A test project" in result

    def test_generic_merge_attributes_content_to_sources(self, tmp_path):
        """Test _generic_merge attributes content to correct source labels."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "jupyter": "## Overview\n\nNotebook content.",
            "pptx": "## Overview\n\nSlide content.",
        }
        result = builder._generic_merge(skill_mds)

        # Check source labels appear
        assert "Jupyter Notebook" in result
        assert "PowerPoint Presentation" in result

    def test_generic_merge_single_source_section(self, tmp_path):
        """Test section unique to one source has 'From <Label>' attribution."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "manpage": "## Synopsis\n\ngit [options]",
        }
        result = builder._generic_merge(skill_mds)

        assert "*From Man Page*" in result
        assert "## Synopsis" in result

    def test_generic_merge_multi_source_section(self, tmp_path):
        """Test section shared by multiple sources gets sub-headings per source."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "asciidoc": "## Quick Reference\n\nAsciiDoc quick ref.",
            "html": "## Quick Reference\n\nHTML quick ref.",
        }
        result = builder._generic_merge(skill_mds)

        # Both sources should be attributed under the shared section
        assert "### From AsciiDoc Document" in result
        assert "### From HTML Document" in result

    def test_generic_merge_footer(self, tmp_path):
        """Test _generic_merge ends with the standard footer."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "rss": "## Feeds\n\nSome feeds.",
        }
        result = builder._generic_merge(skill_mds)
        assert "Generated by Skill Seeker" in result

    def test_generic_merge_merged_from_line(self, tmp_path):
        """Test _generic_merge includes 'Merged from:' with correct labels."""
        builder = self._make_builder(tmp_path)
        skill_mds = {
            "confluence": "## Pages\n\nWiki pages.",
            "notion": "## Databases\n\nNotion DBs.",
        }
        result = builder._generic_merge(skill_mds)

        assert "*Merged from: Confluence Wiki, Notion Page*" in result

    def test_append_extra_sources_adds_sections(self, tmp_path):
        """Test _append_extra_sources adds new sections to base content."""
        builder = self._make_builder(tmp_path)
        base_content = "# Test\n\nIntro.\n\n## Main Section\n\nContent.\n\n---\n\n*Footer*\n"
        skill_mds = {
            "epub": "## Chapters\n\nChapter list.\n\n## Key Concepts\n\nConcept A.",
        }
        result = builder._append_extra_sources(base_content, skill_mds, {"epub"})

        # The extra source content should be inserted before the footer separator
        assert "EPUB E-book Content" in result
        assert "Chapters" in result
        assert "Key Concepts" in result
        # Original content should still be present
        assert "# Test" in result
        assert "## Main Section" in result

    def test_append_extra_sources_preserves_footer(self, tmp_path):
        """Test _append_extra_sources keeps the footer intact."""
        builder = self._make_builder(tmp_path)
        base_content = "# Test\n\n---\n\n*Footer*\n"
        skill_mds = {
            "chat": "## Messages\n\nChat history.",
        }
        result = builder._append_extra_sources(base_content, skill_mds, {"chat"})

        assert "*Footer*" in result

    def test_source_labels_include_retained_public_types(self):
        """Test _SOURCE_LABELS contains the retained public source types."""
        expected = {
            "documentation",
            "github",
            "pdf",
            "word",
            "video",
            "local",
            "html",
            "asciidoc",
            "pptx",
            "confluence",
            "chat",
        }
        assert expected.issubset(set(UnifiedSkillBuilder._SOURCE_LABELS.keys()))

    def test_source_labels_values_are_nonempty_strings(self):
        """Test all _SOURCE_LABELS values are non-empty strings."""
        for key, label in UnifiedSkillBuilder._SOURCE_LABELS.items():
            assert isinstance(label, str), f"Label for '{key}' is not a string"
            assert len(label) > 0, f"Label for '{key}' is empty"


# ---------------------------------------------------------------------------
# 4. New source types accessible via 'create' command
# ---------------------------------------------------------------------------
# Individual scraper CLI commands (jupyter, html, etc.) were removed in the
# Grand Unification refactor.  All 17 source types are now accessed via
# `yonyou-doc2skill create`.  The routing is tested in TestCreateCommandRouting.


# ---------------------------------------------------------------------------
# 5. SourceDetector.validate_source — new types
# ---------------------------------------------------------------------------


class TestSourceDetectorValidation:
    """Test validate_source for new file-based source types."""

    def test_validation_passes_for_existing_html(self, tmp_path):
        """Test validation passes for an existing .html file."""
        html = tmp_path / "page.html"
        html.write_text("<html></html>")

        info = SourceInfo(
            type="html",
            parsed={"file_path": str(html)},
            suggested_name="page",
            raw_input=str(html),
        )
        SourceDetector.validate_source(info)

    def test_validation_raises_for_nonexistent_pptx(self):
        """Test validation raises ValueError for non-existent pptx."""
        info = SourceInfo(
            type="pptx",
            parsed={"file_path": "/nonexistent/slides.pptx"},
            suggested_name="slides",
            raw_input="/nonexistent/slides.pptx",
        )
        with pytest.raises(ValueError, match="does not exist"):
            SourceDetector.validate_source(info)

    def test_validation_raises_for_nonexistent_asciidoc(self):
        """Test validation raises ValueError for non-existent asciidoc."""
        info = SourceInfo(
            type="asciidoc",
            parsed={"file_path": "/nonexistent/doc.adoc"},
            suggested_name="doc",
            raw_input="/nonexistent/doc.adoc",
        )
        with pytest.raises(ValueError, match="does not exist"):
            SourceDetector.validate_source(info)

    def test_validation_passes_for_directory_types(self, tmp_path):
        """Test validation passes when source is a directory (e.g., html dir)."""
        html_dir = tmp_path / "pages"
        html_dir.mkdir()

        info = SourceInfo(
            type="html",
            parsed={"file_path": str(html_dir)},
            suggested_name="pages",
            raw_input=str(html_dir),
        )
        # The validator allows directories for these types (isfile or isdir)
        SourceDetector.validate_source(info)


# ---------------------------------------------------------------------------
# 6. CreateCommand._route_generic coverage
# ---------------------------------------------------------------------------


class TestCreateCommandRouting:
    """Test that CreateCommand uses get_converter for all source types."""

    NEW_SOURCE_TYPES = [
        "html",
        "asciidoc",
        "pptx",
        "confluence",
        "chat",
    ]

    def test_get_converter_handles_all_new_types(self):
        """Test get_converter returns a converter for each new source type."""
        from yonyou_doc2skill.cli.skill_converter import get_converter

        for source_type in self.NEW_SOURCE_TYPES:
            # get_converter should not raise for known types
            # (it may raise ImportError for missing optional deps, which is OK)
            try:
                converter_cls = get_converter(source_type, {"name": "test"})
                assert converter_cls is not None, f"get_converter returned None for '{source_type}'"
            except ImportError:
                # Optional dependency not installed - that's fine
                pass

    def test_get_converter_rejects_removed_public_types(self):
        """Removed public source types should no longer resolve to converters."""
        from yonyou_doc2skill.cli.skill_converter import get_converter

        removed_types = ["epub", "jupyter", "openapi", "rss", "manpage", "notion"]

        for source_type in removed_types:
            with pytest.raises(ValueError, match="Unknown source type"):
                get_converter(source_type, {"name": "test"})

    def test_route_to_scraper_uses_get_converter(self):
        """Test _route_to_scraper delegates to get_converter (not per-type branches)."""
        import inspect

        source = inspect.getsource(
            __import__(
                "yonyou_doc2skill.cli.create_command",
                fromlist=["CreateCommand"],
            ).CreateCommand._route_to_scraper
        )
        assert "get_converter" in source, (
            "_route_to_scraper should use get_converter for unified routing"
        )

    @pytest.mark.parametrize("source_type", ["epub", "jupyter", "openapi", "rss", "manpage", "notion"])
    def test_build_config_rejects_retired_source_types(self, source_type):
        """Retired source types should not be buildable through create flow."""
        ExecutionContext.reset()
        try:
            cmd = CreateCommand(
                Namespace(source="dummy"),
            )
            cmd.source_info = SourceInfo(
                type=source_type,
                parsed={"file_path": "dummy"},
                suggested_name="dummy",
                raw_input="dummy",
            )

            with pytest.raises(ValueError, match="Unsupported source type"):
                cmd._build_config(source_type, ExecutionContext.get())
        finally:
            ExecutionContext.reset()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
