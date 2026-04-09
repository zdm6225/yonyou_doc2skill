# Official Yonyou Doc2Skill Wrapper Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the official `skills/yonyou-doc2skill/SKILL.md` wrapper skill so end users can use it to generate their own skills through a locally installed `yonyou-doc2skill` CLI.

**Architecture:** Keep the wrapper skill thin. It should explain prerequisites, route supported source types, and instruct the agent to invoke local `yonyou-doc2skill create` and optional `package` commands. Update only the official skill content plus the minimal docs/tests needed to keep the public product surface aligned.

**Tech Stack:** Markdown skill file, existing Python/pytest test suite, existing local CLI (`yonyou-doc2skill`)

---

### Task 1: Tighten the official skill scope in tests first

**Files:**
- Modify: `tests/test_package_structure.py`
- Test: `tests/test_package_structure.py`

- [ ] **Step 1: Write the failing test**

Add assertions that the official skill content exists and reflects the wrapper-skill behavior:

```python
    def test_official_skill_describes_local_wrapper_workflow(self):
        root = Path(__file__).parent.parent
        skill_text = (root / "skills" / "yonyou-doc2skill" / "SKILL.md").read_text(encoding="utf-8")

        lowered = skill_text.lower()
        assert "yonyou-doc2skill create" in lowered
        assert "yonyou-doc2skill package" in lowered
        assert "local" in lowered
        assert "confluence" in lowered
        assert "chat" in lowered
        assert "epub" not in lowered
        assert "jupyter" not in lowered
        assert "openapi" not in lowered
        assert "rss" not in lowered
        assert "notion" not in lowered
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_package_structure.py::TestPackageMetadata::test_official_skill_describes_local_wrapper_workflow -v`
Expected: FAIL because the current skill still describes the broader inherited tool surface.

- [ ] **Step 3: Write minimal implementation**

Do not implement yet. First confirm the red state, then update the official skill content in Task 2.

- [ ] **Step 4: Run test to verify it still fails before implementation**

Run: `pytest tests/test_package_structure.py::TestPackageMetadata::test_official_skill_describes_local_wrapper_workflow -v`
Expected: FAIL

- [ ] **Step 5: Commit**

```bash
git add tests/test_package_structure.py
git commit -m "test add wrapper skill coverage"
```

### Task 2: Rewrite the official skill as a local wrapper

**Files:**
- Modify: `skills/yonyou-doc2skill/SKILL.md`
- Test: `tests/test_package_structure.py`

- [ ] **Step 1: Write the failing test**

Use the failing test from Task 1 as the guardrail. Do not add a second test yet.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_package_structure.py::TestPackageMetadata::test_official_skill_describes_local_wrapper_workflow -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Replace the current skill content with a concise local-wrapper skill:

```md
---
name: yonyou-doc2skill
description: Use this skill when the user wants to generate a new skill from documentation, a repository, a local project, a PDF, a Word file, HTML, AsciiDoc, PowerPoint, video, Confluence, or chat exports through the locally installed yonyou-doc2skill CLI.
---

# Yonyou Doc2Skill

Use this skill to turn supported knowledge sources into a new skill by calling the local `yonyou-doc2skill` command.

## Prerequisites

- `yonyou-doc2skill` is installed locally and available on `PATH`
- the agent can read the user-provided local files or repository paths
- if the source is Confluence or chat exports, the required credentials or export files are already available locally

## Supported Sources

- documentation websites
- GitHub repositories
- local codebases
- PDF
- Word `.docx`
- local HTML
- AsciiDoc
- PowerPoint `.pptx`
- video URLs or local video files
- Confluence
- Slack or Discord chat exports

## Routing Rules

- use `yonyou-doc2skill create <source> --name <skill_name>` as the default path
- choose a short, filesystem-safe `--name`
- keep `--enhance-level 0` unless the user explicitly asks for enhancement
- use `yonyou-doc2skill package <output_dir>` only if the user asks for a packaged artifact

## Command Templates

```bash
yonyou-doc2skill create https://docs.example.com --name my-docs-skill --enhance-level 0
yonyou-doc2skill create owner/repo --name repo-skill --enhance-level 0
yonyou-doc2skill create /path/to/project --name local-project-skill --enhance-level 0
yonyou-doc2skill create /path/to/file.pdf --name pdf-skill --enhance-level 0
yonyou-doc2skill create /path/to/page.html --name html-skill --enhance-level 0
yonyou-doc2skill confluence --base-url https://wiki.example.com --space-key TEAM --name team-wiki
yonyou-doc2skill package output/my-docs-skill
```

## Expected Output

- extracted data JSON in `output/<name>_extracted.json`
- skill directory in `output/<name>/`
- main skill file at `output/<name>/SKILL.md`
- references under `output/<name>/references/`

## Working Style

- first confirm the source and target skill name
- then run the narrowest command that fits the request
- report the generated output path back to the user
- if packaging was requested, report the packaged artifact path too
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_package_structure.py::TestPackageMetadata::test_official_skill_describes_local_wrapper_workflow -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/yonyou-doc2skill/SKILL.md tests/test_package_structure.py
git commit -m "feat add official wrapper skill"
```

### Task 3: Align the bootstrap script and docs with the wrapper skill

**Files:**
- Modify: `scripts/bootstrap_skill.sh`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Test: `tests/test_package_structure.py`

- [ ] **Step 1: Write the failing test**

Add a test that the product docs point at the official skill directory and local-install model:

```python
    def test_public_docs_describe_official_skill_delivery_model(self):
        root = Path(__file__).parent.parent
        readme = (root / "README.md").read_text(encoding="utf-8").lower()
        readme_zh = (root / "README.zh-CN.md").read_text(encoding="utf-8").lower()

        assert "skills/yonyou-doc2skill" in readme
        assert "skills/yonyou-doc2skill" in readme_zh
        assert "install" in readme
        assert "本地安装" in readme_zh
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_package_structure.py::TestPackageMetadata::test_public_docs_describe_official_skill_delivery_model -v`
Expected: FAIL because the current docs do not yet explicitly describe the wrapper-skill delivery model.

- [ ] **Step 3: Write minimal implementation**

Make these focused updates:

```bash
# scripts/bootstrap_skill.sh
# keep SKILL_NAME="yonyou-doc2skill"
# add a final note that the generated official skill belongs under:
#   skills/yonyou-doc2skill/

# README.md and README.zh-CN.md
# add a short section that explains:
# 1. users install yonyou-doc2skill locally
# 2. users install the official skill from skills/yonyou-doc2skill/
# 3. the skill calls local yonyou-doc2skill create/package commands
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_package_structure.py::TestPackageMetadata::test_public_docs_describe_official_skill_delivery_model -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/bootstrap_skill.sh README.md README.zh-CN.md tests/test_package_structure.py
git commit -m "docs describe official wrapper skill delivery"
```

### Task 4: Full verification and smoke execution

**Files:**
- Verify only

- [ ] **Step 1: Run focused test suite**

Run: `pytest tests/test_package_structure.py tests/test_cli_parsers.py tests/test_new_source_types.py tests/test_source_detector.py -q`
Expected: all pass

- [ ] **Step 2: Run wrapper-skill smoke command**

Run: `yonyou-doc2skill create /Users/yonyou/sandbox/yonyou_doc2skill/tmp_gfwiki_22539572.html --name smoke-official-wrapper --enhance-level 0`
Expected: generated output under `output/smoke-official-wrapper/`

- [ ] **Step 3: Verify official skill file exists**

Run: `test -f skills/yonyou-doc2skill/SKILL.md && echo OK`
Expected: `OK`

- [ ] **Step 4: Verify docs mention official skill path**

Run: `rg -n "skills/yonyou-doc2skill" README.md README.zh-CN.md scripts/bootstrap_skill.sh`
Expected: at least one hit in each file

- [ ] **Step 5: Commit**

```bash
git add skills/yonyou-doc2skill/SKILL.md README.md README.zh-CN.md scripts/bootstrap_skill.sh tests/test_package_structure.py
git commit -m "chore verify official wrapper skill delivery"
```

