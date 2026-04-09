# Embedded Skill Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the published `skills/yonyou-doc2skill` package bootstrap and run its own embedded Python runtime on first use while preserving the existing `yonyou-doc2skill` CLI.

**Architecture:** Add a skill-local bootstrap script, a skill-local run script, and a packaged embedded runtime copied from the Python package tree. The embedded scripts create and reuse a skill-private `.runtime/.venv`, print explicit initialization progress, and execute the packaged runtime via the local interpreter without changing the existing CLI path.

**Tech Stack:** Python 3, virtualenv via `python3 -m venv`, argparse, subprocess, shutil, pytest

---

## File Map

- Create: `skills/yonyou-doc2skill/requirements.txt`
- Create: `skills/yonyou-doc2skill/scripts/bootstrap.py`
- Create: `skills/yonyou-doc2skill/scripts/run.py`
- Create: `tests/test_embedded_skill_runtime.py`
- Modify: `skills/yonyou-doc2skill/SKILL.md`
- Modify: `tests/test_package_structure.py`
- Modify: `pyproject.toml`
- Modify: `src/yonyou_doc2skill/cli/package_skill.py`

### Task 1: Add failing tests for embedded skill package shape

**Files:**
- Modify: `tests/test_package_structure.py`
- Create: `tests/test_embedded_skill_runtime.py`

- [ ] **Step 1: Write the failing package-structure tests**

```python
def test_official_skill_includes_embedded_runtime_files():
    skill_dir = Path("skills/yonyou-doc2skill")
    assert (skill_dir / "requirements.txt").exists()
    assert (skill_dir / "scripts" / "bootstrap.py").exists()
    assert (skill_dir / "scripts" / "run.py").exists()
```

- [ ] **Step 2: Write the failing bootstrap/runtime behavior tests**

```python
def test_bootstrap_creates_runtime_marker(tmp_path):
    skill_dir = tmp_path / "skill"
    ...
    result = run_bootstrap(skill_dir)
    assert (skill_dir / ".runtime" / "initialized.json").exists()
```

```python
def test_run_script_skips_bootstrap_after_initialization(tmp_path):
    skill_dir = tmp_path / "skill"
    ...
    result = run_embedded(skill_dir, ["create", "input", "--name", "demo"])
    assert "Step 1/6" not in result.stdout
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_package_structure.py tests/test_embedded_skill_runtime.py -q
```

Expected:
- missing `requirements.txt`
- missing `scripts/bootstrap.py`
- missing `scripts/run.py`
- runtime helper import/execution failures

- [ ] **Step 4: Commit**

```bash
git add tests/test_package_structure.py tests/test_embedded_skill_runtime.py
git commit -m "test add embedded skill runtime coverage"
```

### Task 2: Add skill-local bootstrap and run scripts

**Files:**
- Create: `skills/yonyou-doc2skill/requirements.txt`
- Create: `skills/yonyou-doc2skill/scripts/bootstrap.py`
- Create: `skills/yonyou-doc2skill/scripts/run.py`

- [ ] **Step 1: Add the embedded requirements file**

```text
beautifulsoup4
requests
PyYAML
pydantic
pydantic-settings
python-dotenv
pathspec
Pygments
GitPython
PyGithub
PyMuPDF
Pillow
click
schedule
networkx
```

- [ ] **Step 2: Implement bootstrap progress + private venv creation**

```python
def main() -> int:
    print_step(1, "Checking Python runtime")
    python_exe = sys.executable or shutil.which("python3")
    ...
    print_step(2, "Preparing local environment")
    venv.create(str(venv_dir), with_pip=True, clear=False)
    print_step(3, "Installing dependencies")
    subprocess.run([python_bin, "-m", "pip", "install", "-r", str(requirements)], check=True)
    print_step(4, "Verifying runtime")
    subprocess.run([python_bin, "-c", "import requests, bs4"], check=True)
    write_initialized_marker(...)
```

- [ ] **Step 3: Implement run wrapper with auto-bootstrap**

```python
def main() -> int:
    args = sys.argv[1:]
    print_step(5, "Preparing requested command")
    if not is_initialized():
        code = run_bootstrap()
        if code != 0:
            return code
    print_step(6, "Running generation")
    cmd = [str(python_bin), "-m", "yonyou_doc2skill.cli.main", *args]
    return subprocess.run(cmd, cwd=skill_root).returncode
```

- [ ] **Step 4: Run targeted tests to verify they pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_embedded_skill_runtime.py -q
```

Expected:
- bootstrap tests pass
- run wrapper tests pass

- [ ] **Step 5: Commit**

```bash
git add skills/yonyou-doc2skill/requirements.txt skills/yonyou-doc2skill/scripts/bootstrap.py skills/yonyou-doc2skill/scripts/run.py tests/test_embedded_skill_runtime.py
git commit -m "feat add embedded skill bootstrap runtime"
```

### Task 3: Package the embedded runtime into the published skill

**Files:**
- Modify: `src/yonyou_doc2skill/cli/package_skill.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write the failing packaging test**

```python
def test_official_skill_package_includes_runtime_tree(tmp_path):
    ...
    package_skill(...)
    assert (packaged_skill / "runtime" / "yonyou_doc2skill").exists()
```

- [ ] **Step 2: Run targeted test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_package_structure.py -q
```

Expected:
- packaged skill does not yet include embedded runtime tree

- [ ] **Step 3: Implement runtime packaging**

```python
runtime_src = project_root / "src" / "yonyou_doc2skill"
runtime_dst = skill_dir / "runtime" / "yonyou_doc2skill"
shutil.copytree(runtime_src, runtime_dst, dirs_exist_ok=True)
```

Also ensure packaging excludes:
- `.pyc`
- `__pycache__`
- test files

- [ ] **Step 4: Run package-structure tests to verify they pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_package_structure.py -q
```

Expected:
- embedded runtime files and layout pass

- [ ] **Step 5: Commit**

```bash
git add src/yonyou_doc2skill/cli/package_skill.py pyproject.toml tests/test_package_structure.py
git commit -m "feat package embedded runtime with official skill"
```

### Task 4: Update the official skill instructions

**Files:**
- Modify: `skills/yonyou-doc2skill/SKILL.md`

- [ ] **Step 1: Replace global CLI assumptions with local script flow**

```markdown
- run `python3 scripts/run.py create ...`
- first execution may initialize the runtime automatically
- initialization progress is printed step-by-step
```

- [ ] **Step 2: Add command templates for embedded execution**

```bash
python3 scripts/run.py create https://docs.example.com --name my-docs-skill --enhance-level 0
python3 scripts/run.py confluence --base-url https://wiki.example.com --space-key TEAM --token "$TOKEN" --name team-wiki
python3 scripts/run.py package output/my-docs-skill
```

- [ ] **Step 3: Run a focused structure/doc test**

Run:

```bash
.venv/bin/python -m pytest tests/test_package_structure.py -q
```

Expected:
- the official skill content references local scripts and embedded initialization

- [ ] **Step 4: Commit**

```bash
git add skills/yonyou-doc2skill/SKILL.md tests/test_package_structure.py
git commit -m "docs update official skill for embedded runtime"
```

### Task 5: Verify end-to-end behavior

**Files:**
- Reuse: `skills/yonyou-doc2skill/`
- Reuse: `tests/test_embedded_skill_runtime.py`

- [ ] **Step 1: Run the full targeted test suite**

Run:

```bash
.venv/bin/python -m pytest tests/test_package_structure.py tests/test_cli_parsers.py tests/test_confluence_scraper.py tests/test_embedded_skill_runtime.py -q
```

Expected:
- all tests pass

- [ ] **Step 2: Run direct CLI smoke test**

Run:

```bash
.venv/bin/yonyou-doc2skill create /Users/yonyou/sandbox/yonyou_doc2skill/tmp_gfwiki_22539572.html --name smoke-cli-still-works --enhance-level 0
```

Expected:
- skill generated under `output/smoke-cli-still-works/`

- [ ] **Step 3: Run embedded skill bootstrap smoke test**

Run:

```bash
cd skills/yonyou-doc2skill
python3 scripts/run.py create /Users/yonyou/sandbox/yonyou_doc2skill/tmp_gfwiki_22539572.html --name smoke-embedded-skill --enhance-level 0
```

Expected:
- first run prints Step 1/6 through Step 6/6
- `.runtime/initialized.json` is created
- skill generated under `skills/yonyou-doc2skill/output/smoke-embedded-skill/` or configured output path

- [ ] **Step 4: Run embedded skill second-use smoke test**

Run:

```bash
cd skills/yonyou-doc2skill
python3 scripts/run.py create /Users/yonyou/sandbox/yonyou_doc2skill/tmp_gfwiki_22539572.html --name smoke-embedded-skill-second --enhance-level 0
```

Expected:
- skips bootstrap steps 1/6 through 4/6
- continues directly into command preparation and generation

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat ship embedded skill runtime"
```
