# Yonyou Doc2Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand the upstream fork into the external-facing `Yonyou Doc2Skill` product, expose `yonyou-doc2skill create ...` as the primary CLI, and remove EPUB, Jupyter, OpenAPI, RSS, Man page, and Notion from the public product surface.

**Architecture:** Keep the current package/module layout to minimize regression risk. Apply a surface-first productization pass: rebrand package metadata and entry points, remove the six unsupported source types from detector/parser/docs/tests, and preserve internal implementation files unless they are required for public packaging cleanup.

**Tech Stack:** Python 3.10+, setuptools/pyproject, argparse-based CLI, pytest, markdown docs.

---

### Task 1: Rebrand Package Metadata And CLI Entry Points

**Files:**
- Modify: `pyproject.toml`
- Modify: `.codex-plugin/plugin.json`
- Test: `tests/test_package_structure.py`

- [ ] **Step 1: Write the failing test**

```python
from yonyou_doc2skill.cli.main import create_parser


def test_main_cli_still_builds_after_rebrand():
    parser = create_parser()
    assert parser is not None
    assert parser.prog == "yonyou-doc2skill"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_package_structure.py -k rebrand -v`
Expected: FAIL because the parser program name and packaging metadata still reference `yonyou-doc2skill`.

- [ ] **Step 3: Update package identity and script names**

```toml
[project]
name = "yonyou-doc2skill"

[project.scripts]
yonyou-doc2skill = "yonyou_doc2skill.cli.main:main"
yonyou-doc2skill-create = "yonyou_doc2skill.cli.create_command:main"
yonyou-doc2skill-enhance = "yonyou_doc2skill.cli.enhance_command:main"
yonyou-doc2skill-package = "yonyou_doc2skill.cli.package_skill:main"
```

```json
{
  "name": "yonyou-doc2skill",
  "interface": {
    "displayName": "Yonyou Doc2Skill",
    "shortDescription": "Convert docs and repos into AI-ready skills"
  }
}
```

- [ ] **Step 4: Update CLI program naming in main entrypoint**

```python
parser = argparse.ArgumentParser(
    prog="yonyou-doc2skill",
    description="Convert documentation, repositories, and enterprise knowledge into AI skills",
)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/test_package_structure.py -v`
Expected: PASS with updated package identity checks and parser program assertions.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .codex-plugin/plugin.json src/yonyou_doc2skill/cli/main.py tests/test_package_structure.py
git commit -m "feat: rebrand package as yonyou-doc2skill"
```

### Task 2: Remove Unsupported Source Types From Public CLI Surface

**Files:**
- Modify: `src/yonyou_doc2skill/cli/source_detector.py`
- Modify: `src/yonyou_doc2skill/cli/skill_converter.py`
- Modify: `src/yonyou_doc2skill/cli/parsers/__init__.py`
- Modify: `src/yonyou_doc2skill/cli/main.py`
- Modify: `tests/test_new_source_types.py`
- Modify: `tests/test_source_detector.py`
- Modify: `tests/test_cli_parsers.py`

- [ ] **Step 1: Write the failing tests**

```python
import pytest

from yonyou_doc2skill.cli.parsers import get_parser_names
from yonyou_doc2skill.cli.source_detector import SourceDetector


def test_removed_sources_not_detected():
    with pytest.raises(ValueError):
        SourceDetector.detect("book.epub")
    with pytest.raises(ValueError):
        SourceDetector.detect("analysis.ipynb")
    with pytest.raises(ValueError):
        SourceDetector.detect("blog.rss")


def test_removed_dedicated_commands_not_registered():
    names = get_parser_names()
    assert "notion" not in names
```

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `python3 -m pytest tests/test_new_source_types.py tests/test_cli_parsers.py -k "epub or jupyter or openapi or rss or manpage or notion" -v`
Expected: FAIL because those source types are still accepted and/or documented by the current public contract.

- [ ] **Step 3: Remove detection and public registration for unsupported sources**

```python
# source_detector.py
if source.endswith(".pdf"):
    return cls._detect_pdf(source)

if source.endswith(".docx"):
    return cls._detect_word(source)

if source.lower().endswith((".html", ".htm")):
    return cls._detect_html(source)

if source.endswith(".pptx"):
    return cls._detect_pptx(source)
```

```python
# parsers/__init__.py
PARSERS = [
    CreateParser(),
    DoctorParser(),
    ConfigParser(),
    ConfluenceParser(),
    EnhanceParser(),
    ...
]
```

```python
# skill_converter.py
CONVERTER_REGISTRY = {
    "web": (...),
    "github": (...),
    "pdf": (...),
    "word": (...),
    "video": (...),
    "local": (...),
    "html": (...),
    "asciidoc": (...),
    "pptx": (...),
    "confluence": (...),
    "chat": (...),
    "config": (...),
}
```

- [ ] **Step 4: Update parser and detector test expectations**

```python
removed_commands = [
    "scrape",
    "github",
    "pdf",
    "video",
    "word",
    "epub",
    "jupyter",
    "html",
    "openapi",
    "asciidoc",
    "pptx",
    "rss",
    "manpage",
    "notion",
    "chat",
]
```

```python
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
```

- [ ] **Step 5: Run tests to verify public-surface removal passes**

Run: `python3 -m pytest tests/test_new_source_types.py tests/test_source_detector.py tests/test_cli_parsers.py -v`
Expected: PASS with the six removed source types rejected or absent from the public contract.

- [ ] **Step 6: Commit**

```bash
git add src/yonyou_doc2skill/cli/source_detector.py src/yonyou_doc2skill/cli/skill_converter.py src/yonyou_doc2skill/cli/parsers/__init__.py src/yonyou_doc2skill/cli/main.py tests/test_new_source_types.py tests/test_source_detector.py tests/test_cli_parsers.py
git commit -m "feat: narrow public source support for yonyou-doc2skill"
```

### Task 3: Rebrand And Narrow Public Documentation

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/reference/CLI_REFERENCE.md`
- Modify: `docs/user-guide/02-scraping.md`

- [ ] **Step 1: Write the failing docs-surface test**

```python
from pathlib import Path


def test_readme_references_yonyou_doc2skill():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Yonyou Doc2Skill" in readme
    assert "yonyou-doc2skill create book.epub" not in readme
    assert "yonyou-doc2skill notion" not in readme
```

- [ ] **Step 2: Run the docs test to verify it fails**

Run: `python3 -m pytest tests/test_package_structure.py -k readme -v`
Expected: FAIL because README and docs still use upstream branding and include unsupported scenarios.

- [ ] **Step 3: Rewrite user-facing docs around the narrowed product**

```markdown
# Yonyou Doc2Skill

`yonyou-doc2skill` converts documentation, repositories, enterprise wiki content,
and chat exports into AI-ready skill packages.

## Supported Sources

- Documentation websites
- GitHub repositories
- Local codebases
- PDF / Word / HTML / AsciiDoc / PowerPoint
- Video
- Confluence
- Slack / Discord chat exports
```

```markdown
## Removed From This Product Edition

- EPUB
- Jupyter Notebook
- OpenAPI / Swagger
- RSS / Atom
- Man page
- Notion
```

- [ ] **Step 4: Align CLI examples with the new command name**

```bash
yonyou-doc2skill create https://docs.djangoproject.com/
yonyou-doc2skill create django/django
yonyou-doc2skill create ./my-codebase
yonyou-doc2skill confluence --space-key TEAM --name team-wiki
```

- [ ] **Step 5: Run docs-adjacent validation**

Run: `python3 -m pytest tests/test_package_structure.py -v`
Expected: PASS with user-facing docs and package structure assertions updated for `Yonyou Doc2Skill`.

- [ ] **Step 6: Commit**

```bash
git add README.md README.zh-CN.md docs/reference/CLI_REFERENCE.md docs/user-guide/02-scraping.md tests/test_package_structure.py
git commit -m "docs: rebrand public docs for yonyou-doc2skill"
```

### Task 4: Trim Packaging Metadata And Verify Installed Command Surface

**Files:**
- Modify: `pyproject.toml`
- Modify: `tests/test_package_structure.py`
- Modify: `tests/test_cli_parsers.py`

- [ ] **Step 1: Write the failing packaging test**

```python
from pathlib import Path


def test_pyproject_removed_optional_dependencies():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "epub = [" not in pyproject
    assert "jupyter = [" not in pyproject
    assert "notion = [" not in pyproject
    assert "rss = [" not in pyproject
```

- [ ] **Step 2: Run packaging-focused tests to verify they fail**

Run: `python3 -m pytest tests/test_package_structure.py tests/test_cli_parsers.py -k "package or parser" -v`
Expected: FAIL because optional dependencies and command names still reflect the upstream broad product.

- [ ] **Step 3: Remove unsupported optional dependency groups and stale script references**

```toml
[project.optional-dependencies]
docx = [
    "mammoth>=1.6.0",
    "python-docx>=1.1.0",
]

video = [
    "yt-dlp>=2024.12.0",
    "youtube-transcript-api>=1.2.0",
]

confluence = [
    "atlassian-python-api>=3.41.0",
]

chat = [
    "slack-sdk>=3.27.0",
]
```

- [ ] **Step 4: Reinstall locally and verify command help**

Run: `.venv/bin/python -m pip install -e .`
Expected: editable install succeeds and exposes `yonyou-doc2skill`.

Run: `.venv/bin/yonyou-doc2skill --help`
Expected: help output uses `yonyou-doc2skill` branding and does not advertise removed source scenarios.

- [ ] **Step 5: Run verification suite**

Run: `python3 -m pytest tests/test_package_structure.py tests/test_cli_parsers.py tests/test_new_source_types.py tests/test_source_detector.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml tests/test_package_structure.py tests/test_cli_parsers.py tests/test_new_source_types.py tests/test_source_detector.py
git commit -m "chore: trim packaging surface for yonyou-doc2skill"
```

### Task 5: Final End-To-End Verification

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Test: `tests/test_package_structure.py`

- [ ] **Step 1: Reinstall the final editable build**

Run: `.venv/bin/python -m pip install -e .`
Expected: install completes successfully with the renamed package metadata.

- [ ] **Step 2: Verify primary CLI help**

Run: `.venv/bin/yonyou-doc2skill --help`
Expected: PASS and the top-level help shows `yonyou-doc2skill` as the main command.

- [ ] **Step 3: Verify a retained scenario still works**

Run: `.venv/bin/yonyou-doc2skill create /Users/yonyou/sandbox/yonyou_doc2skill/tmp_gfwiki_22539572.html --name smoke-html --enhance-level 0`
Expected: PASS and a skill directory is created under `output/smoke-html/`.

- [ ] **Step 4: Verify a removed scenario is rejected**

Run: `.venv/bin/yonyou-doc2skill create book.epub`
Expected: FAIL with a source detection or unsupported-source error.

- [ ] **Step 5: Run final regression subset**

Run: `python3 -m pytest tests/test_package_structure.py tests/test_cli_parsers.py tests/test_new_source_types.py tests/test_source_detector.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add README.md README.zh-CN.md docs/reference/CLI_REFERENCE.md docs/user-guide/02-scraping.md pyproject.toml src/yonyou_doc2skill/cli/main.py src/yonyou_doc2skill/cli/source_detector.py src/yonyou_doc2skill/cli/skill_converter.py src/yonyou_doc2skill/cli/parsers/__init__.py tests/test_package_structure.py tests/test_cli_parsers.py tests/test_new_source_types.py tests/test_source_detector.py
git commit -m "release: finalize yonyou-doc2skill v1 surface"
```
