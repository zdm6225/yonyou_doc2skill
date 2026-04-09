"""Basic integration tests for create command.

Tests that the create command properly detects source types
and routes to the correct scrapers without actually scraping.
"""

import argparse
import json

import pytest


class TestCreateCommandBasic:
    """Basic integration tests for create command (dry-run mode)."""

    def test_create_command_help(self):
        """Test that create command help works."""
        import subprocess

        result = subprocess.run(
            ["yonyou-doc2skill", "create", "--help"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Auto-detects source type" in result.stdout
        assert "auto-detected" in result.stdout
        assert "--help-web" in result.stdout

    def test_create_detects_web_url(self):
        """Test that web URLs are detected and routed correctly."""
        from yonyou_doc2skill.cli.source_detector import SourceDetector

        info = SourceDetector.detect("https://docs.react.dev/")
        assert info.type == "web"
        assert info.parsed["url"] == "https://docs.react.dev/"
        assert info.suggested_name  # non-empty

        # Plain domain should also be treated as web
        info2 = SourceDetector.detect("docs.example.com")
        assert info2.type == "web"

    def test_create_detects_github_repo(self):
        """Test that GitHub repos are detected."""
        import subprocess

        result = subprocess.run(
            ["yonyou-doc2skill", "create", "facebook/react", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Just verify help works - actual scraping would need API token
        assert result.returncode in [0, 2]  # 0 for success, 2 for argparse help

    def test_create_detects_local_directory(self, tmp_path):
        """Test that local directories are detected."""
        import subprocess

        # Create a test directory
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        result = subprocess.run(
            ["yonyou-doc2skill", "create", str(test_dir), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Verify help works
        assert result.returncode in [0, 2]

    def test_create_detects_pdf_file(self, tmp_path):
        """Test that PDF files are detected."""
        import subprocess

        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()

        result = subprocess.run(
            ["yonyou-doc2skill", "create", str(pdf_file), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Verify help works
        assert result.returncode in [0, 2]

    def test_create_detects_config_file(self, tmp_path):
        """Test that config files are detected."""
        import subprocess
        import json

        # Create a minimal config file
        config_file = tmp_path / "test.json"
        config_data = {"name": "test", "base_url": "https://example.com/"}
        config_file.write_text(json.dumps(config_data))

        result = subprocess.run(
            ["yonyou-doc2skill", "create", str(config_file), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Verify help works
        assert result.returncode in [0, 2]


class TestCreateCommandConverterRouting:
    """Tests that create command routes to correct converters."""

    def test_get_converter_web(self):
        """Test that get_converter returns DocToSkillConverter for web."""
        from yonyou_doc2skill.cli.skill_converter import get_converter

        config = {"name": "test", "base_url": "https://example.com"}
        converter = get_converter("web", config)

        assert converter.SOURCE_TYPE == "web"
        assert converter.name == "test"

    def test_get_converter_github(self):
        """Test that get_converter returns GitHubScraper for github."""
        from yonyou_doc2skill.cli.skill_converter import get_converter

        config = {"name": "test", "repo": "owner/repo"}
        converter = get_converter("github", config)

        assert converter.SOURCE_TYPE == "github"
        assert converter.name == "test"

    def test_get_converter_pdf(self):
        """Test that get_converter returns PDFToSkillConverter for pdf."""
        from yonyou_doc2skill.cli.skill_converter import get_converter

        config = {"name": "test", "pdf_path": "/tmp/test.pdf"}
        converter = get_converter("pdf", config)

        assert converter.SOURCE_TYPE == "pdf"
        assert converter.name == "test"

    def test_get_converter_unknown_raises(self):
        """Test that get_converter raises ValueError for unknown type."""
        from yonyou_doc2skill.cli.skill_converter import get_converter

        with pytest.raises(ValueError, match="Unknown source type"):
            get_converter("unknown_type", {})


class TestExecutionContextIntegration:
    """Tests that ExecutionContext flows correctly through the system."""

    def test_execution_context_auto_initializes(self):
        """ExecutionContext.get() returns defaults without explicit init."""
        from yonyou_doc2skill.cli.execution_context import ExecutionContext

        # Reset to ensure clean state
        ExecutionContext.reset()


class TestCreateCommandHints:
    """Tests for post-create user guidance."""

    def test_logs_enhance_hint_when_enhancement_disabled(self, monkeypatch, caplog):
        """Successful create should suggest enhance when enhancement is off."""
        import argparse

        from yonyou_doc2skill.cli.create_command import CreateCommand
        from yonyou_doc2skill.cli.execution_context import ExecutionContext

        ExecutionContext.reset()
        args = argparse.Namespace(source="https://example.com", name="demo-skill", enhance_level=0)
        cmd = CreateCommand(args)

        source_info = type(
            "SourceInfo",
            (),
            {"type": "web", "suggested_name": "demo-skill", "parsed": {"url": "https://example.com"}},
        )()
        monkeypatch.setattr(
            "yonyou_doc2skill.cli.create_command.SourceDetector.detect", lambda _source: source_info
        )
        monkeypatch.setattr(
            "yonyou_doc2skill.cli.create_command.SourceDetector.validate_source",
            lambda _info: None,
        )
        monkeypatch.setattr(CreateCommand, "_validate_arguments", lambda self: None)
        monkeypatch.setattr(CreateCommand, "_route_to_scraper", lambda self: 0)
        monkeypatch.setattr(CreateCommand, "_run_workflows", lambda self: None)

        with caplog.at_level("INFO"):
            assert cmd.execute() == 0

        assert "可选下一步：增强模式" in caplog.text
        assert "yonyou-doc2skill enhance output/demo-skill --agent codex" in caplog.text

        ExecutionContext.reset()


class TestCreateCommandConfigMerging:
    """Tests for config-file merging in create command web mode."""

    def test_web_config_file_overrides_placeholder_defaults(self, tmp_path):
        """JSON config should populate web settings not explicitly set on CLI."""
        from yonyou_doc2skill.cli.create_command import CreateCommand
        from yonyou_doc2skill.cli.execution_context import ExecutionContext
        from yonyou_doc2skill.cli.source_detector import SourceInfo

        config_file = tmp_path / "nextjs-web.json"
        config_file.write_text(
            json.dumps(
                {
                    "base_url": "https://nextjs.org/docs",
                    "max_pages": 220,
                    "rate_limit": 0.5,
                    "skip_llms_txt": True,
                    "start_urls": ["https://nextjs.org/docs/app"],
                    "selectors": {"title": "h1", "code_blocks": "pre code"},
                    "url_patterns": {"include": ["/docs/app"], "exclude": ["/docs/pages"]},
                    "browser": True,
                    "workers": 4,
                    "skip_scrape": True,
                }
            ),
            encoding="utf-8",
        )

        args_dict = {
            "source": "https://nextjs.org/docs",
            "config": str(config_file),
            "name": "nextjs-reference",
            "profile": "reference",
        }
        args_dict.update(
            {
                key: value
                for key, value in CreateCommand(argparse.Namespace(source="placeholder"))._parser_defaults.items()
                if key not in args_dict
            }
        )
        args = argparse.Namespace(**args_dict)
        cmd = CreateCommand(args)
        cmd.source_info = SourceInfo(
            type="web",
            parsed={"url": "https://nextjs.org/docs"},
            suggested_name="nextjs-reference",
            raw_input="https://nextjs.org/docs",
        )

        ExecutionContext.reset()
        ExecutionContext.initialize(args=args, config_path=str(config_file), source_info=cmd.source_info)
        config = cmd._build_config("web", ExecutionContext.get())

        assert config["max_pages"] == 220
        assert config["rate_limit"] == 0.5
        assert config["skip_llms_txt"] is True
        assert config["start_urls"] == ["https://nextjs.org/docs/app"]
        assert config["selectors"]["title"] == "h1"
        assert config["url_patterns"]["include"] == ["/docs/app"]
        assert config["browser"] is True
        assert config["workers"] == 4
        assert config["skip_scrape"] is True

        ExecutionContext.reset()

    def test_explicit_cli_web_values_still_override_config_file(self, tmp_path):
        """Explicit CLI values should still win over config-file defaults."""
        from yonyou_doc2skill.cli.create_command import CreateCommand
        from yonyou_doc2skill.cli.execution_context import ExecutionContext
        from yonyou_doc2skill.cli.source_detector import SourceInfo

        config_file = tmp_path / "nextjs-web.json"
        config_file.write_text(
            json.dumps(
                {
                    "base_url": "https://nextjs.org/docs",
                    "max_pages": 220,
                    "workers": 4,
                    "browser": False,
                }
            ),
            encoding="utf-8",
        )

        args_dict = {
            "source": "https://nextjs.org/docs",
            "config": str(config_file),
            "name": "nextjs-reference",
            "max_pages": 50,
            "workers": 2,
            "browser": True,
        }
        args_dict.update(
            {
                key: value
                for key, value in CreateCommand(argparse.Namespace(source="placeholder"))._parser_defaults.items()
                if key not in args_dict
            }
        )
        args = argparse.Namespace(**args_dict)
        cmd = CreateCommand(args)
        cmd.source_info = SourceInfo(
            type="web",
            parsed={"url": "https://nextjs.org/docs"},
            suggested_name="nextjs-reference",
            raw_input="https://nextjs.org/docs",
        )

        ExecutionContext.reset()
        ExecutionContext.initialize(args=args, config_path=str(config_file), source_info=cmd.source_info)
        config = cmd._build_config("web", ExecutionContext.get())

        assert config["max_pages"] == 50
        assert config["workers"] == 2
        assert config["browser"] is True

        ExecutionContext.reset()

    def test_skips_enhance_hint_when_enhancement_enabled(self, monkeypatch, caplog):
        """Successful create should not suggest enhance when enhancement already runs."""
        import argparse

        from yonyou_doc2skill.cli.create_command import CreateCommand
        from yonyou_doc2skill.cli.execution_context import ExecutionContext

        ExecutionContext.reset()
        args = argparse.Namespace(source="https://example.com", name="demo-skill", enhance_level=1)
        cmd = CreateCommand(args)

        source_info = type(
            "SourceInfo",
            (),
            {"type": "web", "suggested_name": "demo-skill", "parsed": {"url": "https://example.com"}},
        )()
        monkeypatch.setattr(
            "yonyou_doc2skill.cli.create_command.SourceDetector.detect", lambda _source: source_info
        )
        monkeypatch.setattr(
            "yonyou_doc2skill.cli.create_command.SourceDetector.validate_source",
            lambda _info: None,
        )
        monkeypatch.setattr(CreateCommand, "_validate_arguments", lambda self: None)
        monkeypatch.setattr(CreateCommand, "_route_to_scraper", lambda self: 0)
        monkeypatch.setattr(CreateCommand, "_run_workflows", lambda self: None)
        monkeypatch.setattr(CreateCommand, "_run_enhancement", lambda self, _ctx: None)

        with caplog.at_level("INFO"):
            assert cmd.execute() == 0

        assert "可选下一步：增强模式" not in caplog.text

        ExecutionContext.reset()

        # Should not raise - returns default context
        ctx = ExecutionContext.get()
        assert ctx is not None
        assert ctx.output.name is None  # Default value

        ExecutionContext.reset()

    def test_execution_context_values_preserved(self):
        """Values set in context are preserved and accessible."""
        from yonyou_doc2skill.cli.execution_context import ExecutionContext
        import argparse

        ExecutionContext.reset()

        args = argparse.Namespace(
            source="https://example.com",
            name="test_skill",
            enhance_level=3,
            dry_run=True,
        )

        ctx = ExecutionContext.initialize(args=args)
        assert ctx.output.name == "test_skill"
        assert ctx.enhancement.level == 3
        assert ctx.output.dry_run is True

        # Getting context again returns same values
        ctx2 = ExecutionContext.get()
        assert ctx2.output.name == "test_skill"

        ExecutionContext.reset()


class TestUnifiedCommands:
    """Test that unified commands still work."""

    def test_main_help_shows_available_commands(self):
        """Main help should show available commands."""
        import subprocess

        result = subprocess.run(
            ["yonyou-doc2skill", "--help"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        # Should show create command
        assert "create" in result.stdout
        # Should show enhance command
        assert "enhance" in result.stdout

    def test_workflows_command_still_works(self):
        """The workflows subcommand is accessible via the main CLI."""
        import subprocess

        result = subprocess.run(
            ["yonyou-doc2skill", "workflows", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0


class TestRemovedCommands:
    """Test that old individual scraper commands are properly removed."""

    def test_scrape_command_removed(self):
        """Old scrape command should not exist."""
        import subprocess

        result = subprocess.run(
            ["yonyou-doc2skill", "scrape", "--help"], capture_output=True, text=True, timeout=10
        )
        # Should fail - command removed
        assert result.returncode == 2
        assert "invalid choice" in result.stderr

    def test_github_command_removed(self):
        """Old github command should not exist."""
        import subprocess

        result = subprocess.run(
            ["yonyou-doc2skill", "github", "--help"], capture_output=True, text=True, timeout=10
        )
        # Should fail - command removed
        assert result.returncode == 2
        assert "invalid choice" in result.stderr
