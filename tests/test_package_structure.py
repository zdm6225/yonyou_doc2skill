"""Test suite for Python package structure.

Tests that the package structure is correct and imports work properly.
This ensures modern Python packaging (src/ layout, pyproject.toml) is successful.
"""

import json
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


class TestCliPackage:
    """Test yonyou_doc2skill.cli package structure and imports."""

    def test_cli_package_exists(self):
        """Test that yonyou_doc2skill.cli package can be imported."""
        import yonyou_doc2skill.cli

        assert yonyou_doc2skill.cli is not None

    def test_cli_has_version(self):
        """Test that yonyou_doc2skill.cli package has __version__."""
        import yonyou_doc2skill.cli

        assert hasattr(yonyou_doc2skill.cli, "__version__")
        assert yonyou_doc2skill.cli.__version__ == "3.4.0"

    def test_cli_has_all(self):
        """Test that yonyou_doc2skill.cli package has __all__ export list."""
        import yonyou_doc2skill.cli

        assert hasattr(yonyou_doc2skill.cli, "__all__")
        assert isinstance(yonyou_doc2skill.cli.__all__, list)
        assert len(yonyou_doc2skill.cli.__all__) > 0

    def test_llms_txt_detector_import(self):
        """Test that LlmsTxtDetector can be imported from yonyou_doc2skill.cli."""
        from yonyou_doc2skill.cli import LlmsTxtDetector

        assert LlmsTxtDetector is not None

    def test_llms_txt_downloader_import(self):
        """Test that LlmsTxtDownloader can be imported from yonyou_doc2skill.cli."""
        from yonyou_doc2skill.cli import LlmsTxtDownloader

        assert LlmsTxtDownloader is not None

    def test_llms_txt_parser_import(self):
        """Test that LlmsTxtParser can be imported from yonyou_doc2skill.cli."""
        from yonyou_doc2skill.cli import LlmsTxtParser

        assert LlmsTxtParser is not None

    def test_open_folder_import(self):
        """Test that open_folder can be imported from yonyou_doc2skill.cli (if utils exists)."""
        try:
            from yonyou_doc2skill.cli import open_folder

            # If import succeeds, function should not be None
            assert open_folder is not None
        except ImportError:
            # If utils.py doesn't exist, that's okay for now
            pytest.skip("utils.py not found, skipping open_folder test")

    def test_cli_exports_match_all(self):
        """Test that exported items in __all__ can actually be imported."""
        import yonyou_doc2skill.cli as cli

        for item_name in cli.__all__:
            if item_name == "open_folder" and cli.open_folder is None:
                # open_folder might be None if utils doesn't exist
                continue
            assert hasattr(cli, item_name), f"{item_name} not found in cli package"


class TestMcpPackage:
    """Test yonyou_doc2skill.mcp package structure and imports."""

    def test_mcp_package_exists(self):
        """Test that yonyou_doc2skill.mcp package can be imported."""
        import yonyou_doc2skill.mcp

        assert yonyou_doc2skill.mcp is not None

    def test_mcp_has_version(self):
        """Test that yonyou_doc2skill.mcp package has __version__."""
        import yonyou_doc2skill.mcp

        assert hasattr(yonyou_doc2skill.mcp, "__version__")
        assert yonyou_doc2skill.mcp.__version__ == "3.4.0"

    def test_mcp_has_all(self):
        """Test that yonyou_doc2skill.mcp package has __all__ export list."""
        import yonyou_doc2skill.mcp

        assert hasattr(yonyou_doc2skill.mcp, "__all__")
        assert isinstance(yonyou_doc2skill.mcp.__all__, list)

    def test_mcp_tools_package_exists(self):
        """Test that yonyou_doc2skill.mcp.tools subpackage can be imported."""
        import yonyou_doc2skill.mcp.tools

        assert yonyou_doc2skill.mcp.tools is not None

    def test_mcp_tools_has_version(self):
        """Test that yonyou_doc2skill.mcp.tools has __version__."""
        import yonyou_doc2skill.mcp.tools

        assert hasattr(yonyou_doc2skill.mcp.tools, "__version__")
        assert yonyou_doc2skill.mcp.tools.__version__ == "3.4.0"


class TestPackageStructure:
    """Test overall package structure integrity (src/ layout)."""

    def test_cli_init_file_exists(self):
        """Test that src/yonyou_doc2skill/cli/__init__.py exists."""
        init_file = Path(__file__).parent.parent / "src" / "yonyou_doc2skill" / "cli" / "__init__.py"
        assert init_file.exists(), "src/yonyou_doc2skill/cli/__init__.py not found"

    def test_mcp_init_file_exists(self):
        """Test that src/yonyou_doc2skill/mcp/__init__.py exists."""
        init_file = Path(__file__).parent.parent / "src" / "yonyou_doc2skill" / "mcp" / "__init__.py"
        assert init_file.exists(), "src/yonyou_doc2skill/mcp/__init__.py not found"

    def test_mcp_tools_init_file_exists(self):
        """Test that src/yonyou_doc2skill/mcp/tools/__init__.py exists."""
        init_file = (
            Path(__file__).parent.parent / "src" / "yonyou_doc2skill" / "mcp" / "tools" / "__init__.py"
        )
        assert init_file.exists(), "src/yonyou_doc2skill/mcp/tools/__init__.py not found"

    def test_cli_init_has_docstring(self):
        """Test that yonyou_doc2skill.cli/__init__.py has a module docstring."""
        import yonyou_doc2skill.cli

        assert yonyou_doc2skill.cli.__doc__ is not None
        assert len(yonyou_doc2skill.cli.__doc__) > 50  # Should have substantial documentation

    def test_mcp_init_has_docstring(self):
        """Test that yonyou_doc2skill.mcp/__init__.py has a module docstring."""
        import yonyou_doc2skill.mcp

        assert yonyou_doc2skill.mcp.__doc__ is not None
        assert len(yonyou_doc2skill.mcp.__doc__) > 50  # Should have substantial documentation

    def test_embedded_skill_runtime_is_packaged_for_official_skill(self):
        """Test that the official skill package includes the embedded runtime files."""
        from yonyou_doc2skill.cli.package_skill import package_skill

        root = Path(__file__).parent.parent
        skill_dir = root / "skills" / "yonyou-doc2skill"

        success, package_path = package_skill(skill_dir, open_folder_after=False, skip_quality_check=True)

        assert success is True
        assert package_path is not None
        assert package_path.exists()

        try:
            with zipfile.ZipFile(package_path, "r") as zf:
                names = set(zf.namelist())

            assert "SKILL.md" in names
            assert "scripts/bootstrap_skill.sh" in names
            assert "scripts/skill_header.md" in names
        finally:
            if package_path.exists():
                package_path.unlink()

    def test_embedded_runtime_is_not_packaged_for_regular_skills(self):
        """Test that generated skills stay lightweight and do not receive the embedded runtime."""
        from yonyou_doc2skill.cli.package_skill import package_skill

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "example-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Example Skill\n", encoding="utf-8")
            (skill_dir / "references").mkdir()
            (skill_dir / "scripts").mkdir()
            (skill_dir / "assets").mkdir()

            success, package_path = package_skill(
                skill_dir, open_folder_after=False, skip_quality_check=True
            )

            assert success is True
            assert package_path is not None

            try:
                with zipfile.ZipFile(package_path, "r") as zf:
                    names = set(zf.namelist())

                assert "scripts/bootstrap_skill.sh" not in names
                assert "scripts/skill_header.md" not in names
            finally:
                if package_path.exists():
                    package_path.unlink()

    def test_official_skill_wrapper_mentions_profile_selection(self):
        """The official wrapper skill should document explicit and auto-detected profiles."""
        skill_md = (
            Path(__file__).parent.parent / "skills" / "yonyou-doc2skill" / "SKILL.md"
        ).read_text(encoding="utf-8")

        assert "--profile" in skill_md
        assert "auto-detect" in skill_md.lower()

    def test_official_skill_wrapper_forces_sanitize_init_as_first_reply(self):
        """The official wrapper should force sanitize flows to start with the init panel."""
        root = Path(__file__).parent.parent
        skill_md = (root / "skills" / "yonyou-doc2skill" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        template = (
            root / "skills" / "yonyou-doc2skill" / "templates" / "sanitize-init-panel.md"
        ).read_text(encoding="utf-8")

        for content in (skill_md, template):
            assert "第一条回复只能输出本初始化页" in content
            assert "不要在初始化页之前先总结文件里有哪些敏感信息" in content
            assert "不要在初始化页之前先报告运行时报错、候选项、替换建议或手工替代方案" in content


class TestImportPatterns:
    """Test that various import patterns work correctly."""

    def test_direct_module_import(self):
        """Test importing modules directly."""
        from yonyou_doc2skill.cli import llms_txt_detector, llms_txt_downloader, llms_txt_parser

        assert llms_txt_detector is not None
        assert llms_txt_downloader is not None
        assert llms_txt_parser is not None

    def test_class_import_from_package(self):
        """Test importing classes from package."""
        from yonyou_doc2skill.cli import LlmsTxtDetector, LlmsTxtDownloader, LlmsTxtParser

        assert LlmsTxtDetector.__name__ == "LlmsTxtDetector"
        assert LlmsTxtDownloader.__name__ == "LlmsTxtDownloader"
        assert LlmsTxtParser.__name__ == "LlmsTxtParser"

    def test_package_level_import(self):
        """Test importing entire packages."""
        import yonyou_doc2skill
        import yonyou_doc2skill.cli
        import yonyou_doc2skill.mcp
        import yonyou_doc2skill.mcp.tools

        assert yonyou_doc2skill is not None
        assert yonyou_doc2skill.cli is not None
        assert yonyou_doc2skill.mcp is not None
        assert yonyou_doc2skill.mcp.tools is not None
        assert "yonyou_doc2skill" in sys.modules
        assert "yonyou_doc2skill.cli" in sys.modules
        assert "yonyou_doc2skill.mcp" in sys.modules
        assert "yonyou_doc2skill.mcp.tools" in sys.modules


class TestBackwardsCompatibility:
    """Test that existing code patterns still work."""

    def test_direct_file_import_still_works(self):
        """Test that direct file imports still work (backwards compatible)."""
        # This ensures we didn't break existing code
        from yonyou_doc2skill.cli.llms_txt_detector import LlmsTxtDetector
        from yonyou_doc2skill.cli.llms_txt_downloader import LlmsTxtDownloader
        from yonyou_doc2skill.cli.llms_txt_parser import LlmsTxtParser

        assert LlmsTxtDetector is not None
        assert LlmsTxtDownloader is not None
        assert LlmsTxtParser is not None

    def test_module_path_import_still_works(self):
        """Test that full module path imports still work."""
        import yonyou_doc2skill.cli.llms_txt_detector
        import yonyou_doc2skill.cli.llms_txt_downloader
        import yonyou_doc2skill.cli.llms_txt_parser

        assert yonyou_doc2skill.cli.llms_txt_detector is not None
        assert yonyou_doc2skill.cli.llms_txt_downloader is not None
        assert yonyou_doc2skill.cli.llms_txt_parser is not None


class TestRootPackage:
    """Test root yonyou_doc2skill package."""

    def test_root_package_exists(self):
        """Test that yonyou_doc2skill root package can be imported."""
        import yonyou_doc2skill

        assert yonyou_doc2skill is not None

    def test_root_has_version(self):
        """Test that yonyou_doc2skill root package has __version__."""
        import yonyou_doc2skill

        assert hasattr(yonyou_doc2skill, "__version__")
        assert yonyou_doc2skill.__version__ == "3.4.0"

    def test_root_has_metadata(self):
        """Test that yonyou_doc2skill root package has metadata."""
        import yonyou_doc2skill

        assert hasattr(yonyou_doc2skill, "__author__")
        assert hasattr(yonyou_doc2skill, "__license__")
        assert yonyou_doc2skill.__license__ == "MIT"


class TestCLIEntryPoints:
    """Test that CLI entry points are properly configured."""

    def test_main_cli_module_exists(self):
        """Test that main.py module exists and can be imported."""
        from yonyou_doc2skill.cli import main

        assert main is not None
        assert hasattr(main, "main")
        assert callable(main.main)

    def test_main_cli_has_parser(self):
        """Test that main.py has parser creation function."""
        from yonyou_doc2skill.cli.main import create_parser

        parser = create_parser()
        assert parser is not None
        assert parser.prog == "yonyou-doc2skill"


class TestPackageMetadata:
    """Test that package metadata reflects the Doc2Skill rebrand."""

    def test_project_name_and_scripts(self):
        """Test project name and console scripts use the new brand."""
        root = Path(__file__).parent.parent
        pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

        assert pyproject["project"]["name"] == "yonyou-doc2skill"
        assert pyproject["project"]["description"] == (
            "Yonyou Doc2Skill converts documentation websites, GitHub repositories, and PDFs into AI skills."
        )
        assert pyproject["project"]["authors"] == [{"name": "Yonyou"}]

        scripts = pyproject["project"]["scripts"]
        assert scripts["yonyou-doc2skill"] == "yonyou_doc2skill.cli.main:main"
        assert scripts["yonyou-doc2skill-create"] == "yonyou_doc2skill.cli.create_command:main"
        assert scripts["yonyou-doc2skill-enhance"] == "yonyou_doc2skill.cli.enhance_command:main"
        assert scripts["yonyou-doc2skill-package"] == "yonyou_doc2skill.cli.package_skill:main"
        assert all(not name.startswith("skill-seekers") for name in scripts)

        optional_dependencies = pyproject["project"]["optional-dependencies"]
        assert "epub" not in optional_dependencies
        assert "jupyter" not in optional_dependencies

    def test_project_urls_do_not_reference_upstream_brand(self):
        """Test project URLs are rehomed away from the upstream brand."""
        root = Path(__file__).parent.parent
        pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        urls = pyproject["project"]["urls"]

        for value in urls.values():
            assert "skillseekersweb.com" not in value.lower()
            assert "skill-seekers" not in value.lower()
            assert "yusufkaraaslan" not in value.lower()
        assert urls["Homepage"] == "https://docs.yonyou.example/yonyou-doc2skill"
        assert urls["Repository"] == "https://github.com/yonyou/yonyou-doc2skill"

    def test_plugin_metadata_uses_new_brand(self):
        """Test plugin metadata exposes the new product name."""
        root = Path(__file__).parent.parent
        plugin_json = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        assert plugin_json["name"] == "yonyou-doc2skill"
        assert plugin_json["version"] == "3.4.0"
        assert plugin_json["author"]["name"] == "Yonyou"
        assert plugin_json["author"]["url"] == "https://github.com/yonyou/yonyou-doc2skill"
        assert plugin_json["homepage"] == "https://docs.yonyou.example/yonyou-doc2skill"
        assert plugin_json["repository"] == "https://github.com/yonyou/yonyou-doc2skill"
        assert plugin_json["interface"]["displayName"] == "Yonyou Doc2Skill"
        assert plugin_json["interface"]["shortDescription"] == "Convert docs and repos into AI skills"
        assert plugin_json["interface"]["websiteURL"] == "https://docs.yonyou.example/yonyou-doc2skill"
        plugin_text = json.dumps(plugin_json).lower()
        assert "skillseekersweb.com" not in plugin_text
        assert "skill-seekers" not in plugin_text
        assert "yusufkaraaslan" not in plugin_text

    def test_main_help_epilog_uses_yonyou_url(self):
        """Test the CLI help epilog points at the Yonyou placeholder URL."""
        from yonyou_doc2skill.cli.main import create_parser

        parser = create_parser()

        assert "https://docs.yonyou.example/yonyou-doc2skill" in parser.epilog
        assert "github.com/yusufkaraaslan/skill_seekers" not in parser.epilog.lower()

    def test_public_docs_surface_is_rebranded_and_narrowed(self):
        """Test the public docs only advertise retained source types."""
        root = Path(__file__).parent.parent
        doc_files = [
            root / "README.md",
            root / "README.zh-CN.md",
            root / "docs" / "reference" / "CLI_REFERENCE.md",
            root / "docs" / "user-guide" / "02-scraping.md",
        ]
        disallowed_terms = ["epub", "jupyter", "openapi", "rss", "manpage", "notion"]
        allowed_examples = ["yonyou-doc2skill create", "yonyou-doc2skill package"]

        for doc_file in doc_files:
            content = doc_file.read_text(encoding="utf-8").lower()
            for term in disallowed_terms:
                assert term not in content, f"{doc_file.name} still mentions {term}"

        readme = (root / "README.md").read_text(encoding="utf-8")
        assert "Yonyou Doc2Skill" in readme
        assert any(example in readme for example in allowed_examples)

    def test_official_skill_describes_local_wrapper_workflow(self):
        """Test the official skill describes the supported local wrapper workflow."""
        root = Path(__file__).parent.parent
        skill_text = (root / "skills" / "yonyou-doc2skill" / "SKILL.md").read_text(encoding="utf-8")

        lowered = skill_text.lower()
        assert "python3 scripts/run.py create" in lowered
        assert "python3 scripts/run.py package" in lowered
        assert ".runtime/" in lowered
        assert "local" in lowered
        assert "confluence" in lowered
        assert "chat" in lowered
        assert "epub" not in lowered
        assert "jupyter" not in lowered
        assert "openapi" not in lowered
        assert "rss" not in lowered
        assert "notion" not in lowered

    def test_official_skill_requires_fixed_sanitize_init_panel(self):
        """The official skill should force the fixed sanitize initialization panel."""
        root = Path(__file__).parent.parent
        skill_text = (root / "skills" / "yonyou-doc2skill" / "SKILL.md").read_text(encoding="utf-8")

        assert "脱敏场景的第一条回复只能是初始化选择页" in skill_text
        assert "第一条回复只能输出本初始化页" in skill_text
        assert "推荐选择：1 + 1 + 1" in skill_text
        assert "不要自行改写、压缩、重排这段文案" in skill_text
        assert "不要在初始化页之前先总结文件里有哪些敏感信息" in skill_text
        assert "不要在初始化页之前先报告运行时报错、候选项、替换建议或手工替代方案" in skill_text
        assert "如果第一项选择 3，则只表示“脱敏清单由人工配置”" in skill_text
        assert "第二项、第三项仍严格按本轮选择执行" in skill_text

    def test_public_docs_describe_official_skill_delivery_model(self):
        """Test the public docs explain the official skill plus local CLI model."""
        root = Path(__file__).parent.parent
        readme = (root / "README.md").read_text(encoding="utf-8").lower()
        readme_zh = (root / "README.zh-CN.md").read_text(encoding="utf-8").lower()

        assert "skills/yonyou-doc2skill" in readme
        assert "skills/yonyou-doc2skill" in readme_zh
        assert "install" in readme
        assert "本地安装" in readme_zh

    def test_official_skill_embedded_runtime_files_exist(self):
        """The official published skill should include embedded runtime assets."""
        root = Path(__file__).parent.parent
        skill_dir = root / "skills" / "yonyou-doc2skill"

        assert (skill_dir / "package.json").exists()
        assert (skill_dir / "requirements.txt").exists()
        assert (skill_dir / "scripts" / "bootstrap.py").exists()
        assert (skill_dir / "scripts" / "run.py").exists()
        assert (skill_dir / "runtime" / "yonyou_doc2skill" / "cli" / "main.py").exists()

    def test_delivery_skill_embedded_runtime_files_exist(self):
        """The delivery skill package should include embedded runtime assets."""
        root = Path(__file__).parent.parent
        skill_dir = root / "skills" / "yonyou-knowledge-delivery-boost"

        assert (skill_dir / "package.json").exists()
        assert (skill_dir / "requirements.txt").exists()
        assert (skill_dir / "scripts" / "bootstrap.py").exists()
        assert (skill_dir / "scripts" / "run.py").exists()
        assert (skill_dir / "runtime" / "yonyou_doc2skill" / "cli" / "main.py").exists()

    def test_official_skill_requirements_are_version_locked(self):
        """Embedded runtime dependencies should be pinned for reproducible bootstrap."""
        root = Path(__file__).parent.parent
        requirements = (root / "skills" / "yonyou-doc2skill" / "requirements.txt").read_text(
            encoding="utf-8"
        )

        for raw_line in requirements.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            assert "==" in line, f"Unpinned embedded dependency: {line}"

    def test_delivery_skill_requirements_are_version_locked(self):
        """Delivery skill embedded runtime dependencies should be pinned for reproducible bootstrap."""
        root = Path(__file__).parent.parent
        requirements = (
            root / "skills" / "yonyou-knowledge-delivery-boost" / "requirements.txt"
        ).read_text(encoding="utf-8")

        for raw_line in requirements.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            assert "==" in line, f"Unpinned embedded dependency: {line}"

    def test_embedded_skill_runtime_is_packaged_for_official_skill(self):
        """Packaging the official skill should retain runtime and bootstrap files."""
        from yonyou_doc2skill.cli.package_skill import package_skill

        root = Path(__file__).parent.parent
        skill_dir = root / "skills" / "yonyou-doc2skill"

        success, package_path = package_skill(skill_dir, open_folder_after=False, skip_quality_check=True)

        assert success is True
        assert package_path is not None
        assert package_path.exists()

        try:
            with zipfile.ZipFile(package_path, "r") as zf:
                names = set(zf.namelist())

            assert "SKILL.md" in names
            assert "package.json" in names
            assert "requirements.txt" in names
            assert "scripts/bootstrap.py" in names
            assert "scripts/run.py" in names
            assert "runtime/yonyou_doc2skill/cli/main.py" in names
        finally:
            if package_path.exists():
                package_path.unlink()

    def test_embedded_skill_runtime_is_packaged_for_delivery_skill(self):
        """Packaging the delivery skill should retain runtime and bootstrap files."""
        from yonyou_doc2skill.cli.package_skill import package_skill

        root = Path(__file__).parent.parent
        skill_dir = root / "skills" / "yonyou-knowledge-delivery-boost"

        success, package_path = package_skill(skill_dir, open_folder_after=False, skip_quality_check=True)

        assert success is True
        assert package_path is not None
        assert package_path.exists()

        try:
            with zipfile.ZipFile(package_path, "r") as zf:
                names = set(zf.namelist())

            assert "SKILL.md" in names
            assert "package.json" in names
            assert "requirements.txt" in names
            assert "scripts/bootstrap.py" in names
            assert "scripts/run.py" in names
            assert "runtime/yonyou_doc2skill/cli/main.py" in names
        finally:
            if package_path.exists():
                package_path.unlink()

    def test_delivery_skill_wrapper_mentions_rag_and_delivery_scenarios(self):
        """The delivery wrapper skill should emphasize delivery and RAG use cases."""
        skill_md = (
            Path(__file__).parent.parent / "skills" / "yonyou-knowledge-delivery-boost" / "SKILL.md"
        ).read_text(encoding="utf-8")

        lowered = skill_md.lower()
        assert "rag" in lowered
        assert "交付" in skill_md
        assert "internal-wiki" in lowered

    def test_embedded_runtime_is_not_packaged_for_regular_skills(self):
        """Generated skills stay lightweight and do not receive the embedded runtime."""
        from yonyou_doc2skill.cli.package_skill import package_skill

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "example-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Example Skill\n", encoding="utf-8")
            (skill_dir / "references").mkdir()

            success, package_path = package_skill(
                skill_dir, open_folder_after=False, skip_quality_check=True
            )

            assert success is True
            assert package_path is not None

            try:
                with zipfile.ZipFile(package_path, "r") as zf:
                    names = set(zf.namelist())

                assert "runtime/yonyou_doc2skill/cli/main.py" not in names
                assert "requirements.txt" not in names
            finally:
                if package_path.exists():
                    package_path.unlink()

    def test_runtime_and_docs_surface_do_not_reference_upstream_brand(self):
        """Test runtime/public docs surfaces no longer reference upstream branding."""
        root = Path(__file__).parent.parent
        scan_roots = [
            root / "src",
            root / "docs",
        ]
        excluded_parts = {
            "archive",
            "agents",
            "UML",
            "superpowers",
            "yonyou_doc2skill.egg-info",
            "yonyou_doc2skill.egg-info",
            "__pycache__",
        }
        disallowed_terms = [
            "skill-seekers",
            "skill seekers",
            "skillseekers",
            "yusufkaraaslan",
            ".skill-seekers",
            "~/.config/skill-seekers",
        ]

        for scan_root in scan_roots:
            for path in scan_root.rglob("*"):
                if not path.is_file():
                    continue
                if any(part in excluded_parts for part in path.parts):
                    continue
                if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg"}:
                    continue
                if path.suffix.lower() in {".pyc", ".pyo"}:
                    continue

                content = path.read_text(encoding="utf-8", errors="ignore").lower()
                for term in disallowed_terms:
                    assert term not in content, f"{path} still mentions {term}"
