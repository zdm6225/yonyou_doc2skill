#!/usr/bin/env python3
"""
Test suite for modern CLI command patterns
Tests that all CLI scripts use correct unified CLI commands in usage messages and print statements
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RUNTIME_PACKAGE_DIR = (
    Path(__file__).parent.parent / "skills" / "yonyou-doc2skill" / "runtime" / "yonyou_doc2skill"
)


class TestModernCLICommands(unittest.TestCase):
    """Test that all CLI scripts use modern unified CLI commands"""

    def test_doc_scraper_uses_modern_commands(self):
        """Test doc_scraper.py uses yonyou-doc2skill commands"""
        script_path = RUNTIME_PACKAGE_DIR / "cli" / "doc_scraper.py"

        with open(script_path) as f:
            content = f.read()

        # Should use modern commands
        self.assertIn("yonyou-doc2skill scrape", content)

        # Should NOT use old python3 cli/ pattern
        self.assertNotIn("python3 cli/doc_scraper.py", content)

    def test_enhance_skill_local_uses_modern_commands(self):
        """Test enhance_skill_local.py uses yonyou-doc2skill commands"""
        script_path = RUNTIME_PACKAGE_DIR / "cli" / "enhance_skill_local.py"

        with open(script_path) as f:
            content = f.read()

        # Should use modern commands
        self.assertIn("yonyou-doc2skill", content)

        # Should NOT use old python3 cli/ pattern
        self.assertNotIn("python3 cli/enhance_skill_local.py", content)

    def test_estimate_pages_uses_modern_commands(self):
        """Test estimate_pages.py uses yonyou-doc2skill commands"""
        script_path = RUNTIME_PACKAGE_DIR / "cli" / "estimate_pages.py"

        with open(script_path) as f:
            content = f.read()

        # Should use modern commands
        self.assertIn("yonyou-doc2skill estimate", content)

        # Should NOT use old python3 cli/ pattern
        self.assertNotIn("python3 cli/estimate_pages.py", content)

    def test_package_skill_uses_modern_commands(self):
        """Test package_skill.py uses yonyou-doc2skill commands"""
        script_path = RUNTIME_PACKAGE_DIR / "cli" / "package_skill.py"

        with open(script_path) as f:
            content = f.read()

        # Should use modern commands
        self.assertIn("yonyou-doc2skill package", content)

        # Should NOT use old python3 cli/ pattern
        self.assertNotIn("python3 cli/package_skill.py", content)

    def test_github_scraper_uses_modern_commands(self):
        """Test github_scraper.py uses yonyou-doc2skill commands"""
        script_path = RUNTIME_PACKAGE_DIR / "cli" / "github_scraper.py"

        with open(script_path) as f:
            content = f.read()

        # Should use modern commands
        self.assertIn("yonyou-doc2skill", content)

        # Should NOT use old python3 cli/ pattern
        self.assertNotIn("python3 cli/github_scraper.py", content)


class TestUnifiedCLIEntryPoints(unittest.TestCase):
    """Test that unified CLI entry points work correctly"""

    def test_main_cli_help_output(self):
        """Test yonyou-doc2skill --help works"""
        try:
            result = subprocess.run(
                ["yonyou-doc2skill", "--help"], capture_output=True, text=True, timeout=5
            )

            # Should return successfully
            self.assertIn(
                result.returncode,
                [0, 2],
                f"yonyou-doc2skill --help failed with code {result.returncode}",
            )

            # Should show subcommands
            output = result.stdout + result.stderr
            self.assertIn("scrape", output)
            self.assertIn("github", output)
            self.assertIn("package", output)

        except FileNotFoundError:
            # If yonyou-doc2skill is not installed, skip this test
            self.skipTest("yonyou-doc2skill command not found - install package first")

    def test_main_cli_version_output(self):
        """Test yonyou-doc2skill --version works"""
        try:
            result = subprocess.run(
                ["yonyou-doc2skill", "--version"], capture_output=True, text=True, timeout=5
            )

            # Should return successfully
            self.assertEqual(
                result.returncode, 0, f"yonyou-doc2skill --version failed: {result.stderr}"
            )

            # Should show version
            output = result.stdout + result.stderr
            self.assertIn("3.4.0", output)

        except FileNotFoundError:
            # If yonyou-doc2skill is not installed, skip this test
            self.skipTest("yonyou-doc2skill command not found - install package first")


class TestNoHardcodedPaths(unittest.TestCase):
    """Test that no scripts have hardcoded absolute paths"""

    def test_no_hardcoded_paths_in_cli_scripts(self):
        """Test that CLI scripts don't have hardcoded paths"""
        cli_dir = RUNTIME_PACKAGE_DIR / "cli"

        hardcoded_paths = [
            "/mnt/skills/examples/skill-creator/scripts/",
            "/home/",
            "/Users/",
        ]

        for script_path in cli_dir.glob("*.py"):
            with open(script_path) as f:
                content = f.read()

            for hardcoded_path in hardcoded_paths:
                self.assertNotIn(
                    hardcoded_path,
                    content,
                    f"{script_path.name} contains hardcoded path: {hardcoded_path}",
                )


class TestPackageStructure(unittest.TestCase):
    """Test that package structure is correct"""

    def test_skill_runtime_layout_exists(self):
        """Test that skill runtime package directory exists."""
        self.assertTrue(
            RUNTIME_PACKAGE_DIR.exists(),
            "skills/yonyou-doc2skill/runtime/yonyou_doc2skill/ directory should exist",
        )

    def test_cli_package_exists(self):
        """Test that CLI package exists in the skill runtime."""
        cli_dir = RUNTIME_PACKAGE_DIR / "cli"
        self.assertTrue(
            cli_dir.exists(),
            "skills/yonyou-doc2skill/runtime/yonyou_doc2skill/cli/ directory should exist",
        )

        init_file = cli_dir / "__init__.py"
        self.assertTrue(
            init_file.exists(),
            "skills/yonyou-doc2skill/runtime/yonyou_doc2skill/cli/__init__.py should exist",
        )

    def test_mcp_package_exists(self):
        """Test that MCP package exists in the skill runtime."""
        mcp_dir = RUNTIME_PACKAGE_DIR / "mcp"
        self.assertTrue(
            mcp_dir.exists(),
            "skills/yonyou-doc2skill/runtime/yonyou_doc2skill/mcp/ directory should exist",
        )

        init_file = mcp_dir / "__init__.py"
        self.assertTrue(
            init_file.exists(),
            "skills/yonyou-doc2skill/runtime/yonyou_doc2skill/mcp/__init__.py should exist",
        )

    def test_main_cli_file_exists(self):
        """Test that main.py unified CLI exists"""
        main_file = RUNTIME_PACKAGE_DIR / "cli" / "main.py"
        self.assertTrue(
            main_file.exists(),
            "skills/yonyou-doc2skill/runtime/yonyou_doc2skill/cli/main.py should exist",
        )


if __name__ == "__main__":
    unittest.main()
