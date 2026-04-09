# Skill Profile Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user-visible skill profiles so generated skills can be explicitly targeted or auto-classified instead of always using one generic structure.

**Architecture:** Introduce a small profile detection module plus a profile-aware SKILL.md shaping module, wire them into `create`, and teach the official wrapper skill to request or pass through the profile. Keep the first version rule-based and source-local, with explicit CLI override and low-confidence follow-up handled by the wrapper skill.

**Tech Stack:** Python, argparse, existing create/doc_scraper pipeline, pytest

---

### Task 1: Add Profile Parsing and Detection Primitives

**Files:**
- Create: `src/yonyou_doc2skill/cli/profile_detection.py`
- Modify: `src/yonyou_doc2skill/cli/arguments/create.py`
- Modify: `src/yonyou_doc2skill/cli/create_command.py`
- Test: `tests/test_profile_detection.py`
- Test: `tests/test_cli_parsers.py`

- [ ] **Step 1: Write the failing detection tests**

```python
def test_detect_profile_prefers_reference_for_api_docs():
    from yonyou_doc2skill.cli.profile_detection import detect_skill_profile

    result = detect_skill_profile(
        source_type="web",
        source_value="https://react.dev/reference/react/useState",
        page_signals=["reference", "api", "hooks"],
    )

    assert result.profile == "reference"
    assert result.confidence > 0.5


def test_detect_profile_prefers_internal_wiki_for_confluence():
    from yonyou_doc2skill.cli.profile_detection import detect_skill_profile

    result = detect_skill_profile(
        source_type="confluence",
        source_value="https://wiki.example.com",
        page_signals=["process", "approval", "department"],
    )

    assert result.profile == "internal-wiki"


def test_profile_override_is_preserved_in_create_config():
    from argparse import Namespace
    from yonyou_doc2skill.cli.create_command import CreateCommand

    args = Namespace(source="https://react.dev", profile="reference", description=None)
    command = CreateCommand(args, parser_defaults={"profile": None})
    command.source_info = type("S", (), {"type": "web", "raw_input": "https://react.dev", "suggested_name": "react", "parsed": {"url": "https://react.dev"}})()

    class Ctx:
        class Output:
            name = None
            doc_version = ""
        class Scraping:
            max_pages = 10
            rate_limit = 0.5
            browser = False
            browser_wait_until = "domcontentloaded"
            browser_extra_wait = 0
            workers = 1
            async_mode = False
            resume = False
            fresh = False
            skip_scrape = False
        output = Output()
        scraping = Scraping()

    config = command._build_config("web", Ctx())
    assert config["skill_profile"] == "reference"
```

- [ ] **Step 2: Run detection tests to verify they fail**

Run: `pytest tests/test_profile_detection.py tests/test_cli_parsers.py -q`
Expected: FAIL with missing `profile_detection.py`, missing parser flag, or missing `skill_profile` in config.

- [ ] **Step 3: Add the profile detection module and parser flag**

```python
# src/yonyou_doc2skill/cli/profile_detection.py
from dataclasses import dataclass


PROFILE_CHOICES = (
    "general",
    "tutorial",
    "reference",
    "builder",
    "troubleshooting",
    "internal-wiki",
)


@dataclass(frozen=True)
class ProfileDecision:
    profile: str
    confidence: float
    reasons: list[str]


KEYWORDS = {
    "tutorial": ("getting started", "quick start", "tutorial", "guide", "learn", "introduction"),
    "reference": ("reference", "api", "props", "parameters", "component", "command", "options"),
    "builder": ("build", "generate", "scaffold", "workflow", "implementation", "integration"),
    "troubleshooting": ("error", "debug", "troubleshooting", "warning", "issue", "failed", "fix"),
    "internal-wiki": ("policy", "process", "approval", "role", "department", "internal", "faq", "standard"),
}


def detect_skill_profile(source_type: str, source_value: str, page_signals: list[str] | None = None) -> ProfileDecision:
    signals = " ".join([source_value, *(page_signals or [])]).lower()
    scores = {choice: 0 for choice in PROFILE_CHOICES}

    if source_type == "github":
        scores["builder"] += 3
    elif source_type == "confluence":
        scores["internal-wiki"] += 3
    elif source_type == "web":
        scores["reference"] += 1

    for profile, keywords in KEYWORDS.items():
        scores[profile] += sum(1 for kw in keywords if kw in signals)

    best_profile = max(scores, key=scores.get)
    best_score = scores[best_profile]
    second_score = sorted(scores.values(), reverse=True)[1]
    confidence = 1.0 if best_score == 0 else round(best_score / max(best_score + second_score, 1), 2)
    reasons = [kw for kw in KEYWORDS.get(best_profile, ()) if kw in signals][:5]

    return ProfileDecision(
        profile=best_profile if best_score > 0 else "general",
        confidence=confidence if best_score > 0 else 0.0,
        reasons=reasons,
    )
```

```python
# in src/yonyou_doc2skill/cli/arguments/create.py
parser.add_argument(
    "--profile",
    choices=["general", "tutorial", "reference", "builder", "troubleshooting", "internal-wiki"],
    help="Skill profile to generate. If omitted, Doc2Skill will auto-detect one.",
)
```

```python
# in src/yonyou_doc2skill/cli/create_command.py, inside _build_config()
config["skill_profile"] = getattr(self.args, "profile", None)
```

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `pytest tests/test_profile_detection.py tests/test_cli_parsers.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yonyou_doc2skill/cli/profile_detection.py src/yonyou_doc2skill/cli/arguments/create.py src/yonyou_doc2skill/cli/create_command.py tests/test_profile_detection.py tests/test_cli_parsers.py
git commit -m "feat add skill profile detection primitives"
```

### Task 2: Make Doc Scraper Build Profile-Aware SKILL.md Files

**Files:**
- Create: `src/yonyou_doc2skill/cli/profile_templates.py`
- Modify: `src/yonyou_doc2skill/cli/doc_scraper.py`
- Modify: `skills/yonyou-doc2skill/runtime/yonyou_doc2skill/cli/doc_scraper.py`
- Test: `tests/test_profile_templates.py`
- Test: `tests/test_scraper_features.py`

- [ ] **Step 1: Write the failing template tests**

```python
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
```

```python
def test_doc_scraper_falls_back_to_detected_profile_when_missing_override():
    from yonyou_doc2skill.cli.profile_detection import ProfileDecision
    from yonyou_doc2skill.cli.doc_scraper import DocToSkillConverter

    config = {"name": "react", "base_url": "https://react.dev", "selectors": {"main_content": "article"}}
    converter = DocToSkillConverter(config, dry_run=True)
    converter._detected_profile = ProfileDecision("reference", 0.9, ["reference"])

    assert converter._resolve_skill_profile() == "reference"
```

- [ ] **Step 2: Run the template tests to verify they fail**

Run: `pytest tests/test_profile_templates.py tests/test_scraper_features.py -q`
Expected: FAIL because `profile_templates.py` and `_resolve_skill_profile()` do not exist.

- [ ] **Step 3: Add profile template helpers and integrate them**

```python
# src/yonyou_doc2skill/cli/profile_templates.py
def build_profile_sections(profile: str, skill_name: str) -> str:
    sections = {
        "general": "## Working with This Skill\n\nUse this skill for general questions and implementation support.\n",
        "tutorial": "## Learning Path\n\nStart with foundational concepts, then move to guided examples and practical workflows.\n",
        "reference": "## Quick lookup\n\nUse this skill for API, component, command, and parameter lookup.\n",
        "builder": "## Implementation Workflow\n\nUse this skill when turning the source material into code, config, or repeatable build steps.\n",
        "troubleshooting": "## Troubleshooting Workflow\n\nUse this skill to diagnose failures, interpret errors, and narrow likely root causes.\n",
        "internal-wiki": "## Organization Context\n\nUse this skill to navigate internal terms, responsibilities, processes, and policy guidance.\n",
    }
    return sections.get(profile, sections["general"])
```

```python
# in src/yonyou_doc2skill/cli/doc_scraper.py
from yonyou_doc2skill.cli.profile_detection import detect_skill_profile
from yonyou_doc2skill.cli.profile_templates import build_profile_sections

def _resolve_skill_profile(self) -> str:
    explicit = self.config.get("skill_profile")
    if explicit:
        return explicit
    if hasattr(self, "_detected_profile") and self._detected_profile:
        return self._detected_profile.profile
    return "general"
```

```python
# in create_enhanced_skill_md()
profile = self._resolve_skill_profile()
profile_sections = build_profile_sections(profile, self.name)
content += "\n" + profile_sections
```

```python
# before build_skill() consumes pages
self._detected_profile = detect_skill_profile(
    source_type="web",
    source_value=self.base_url,
    page_signals=[page.get("title", "") for page in self.pages[:50]],
)
```

- [ ] **Step 4: Mirror the same doc scraper changes into the embedded runtime copy**

```bash
cp src/yonyou_doc2skill/cli/doc_scraper.py skills/yonyou-doc2skill/runtime/yonyou_doc2skill/cli/doc_scraper.py
```

- [ ] **Step 5: Run the targeted tests to verify they pass**

Run: `pytest tests/test_profile_templates.py tests/test_scraper_features.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/yonyou_doc2skill/cli/profile_templates.py src/yonyou_doc2skill/cli/doc_scraper.py skills/yonyou-doc2skill/runtime/yonyou_doc2skill/cli/doc_scraper.py tests/test_profile_templates.py tests/test_scraper_features.py
git commit -m "feat add profile-aware skill generation"
```

### Task 3: Surface Profile Decisions in Create Output and Metadata

**Files:**
- Modify: `src/yonyou_doc2skill/cli/create_command.py`
- Modify: `src/yonyou_doc2skill/cli/doc_scraper.py`
- Test: `tests/test_profile_detection.py`

- [ ] **Step 1: Write the failing metadata tests**

```python
def test_auto_detected_profile_is_recorded_in_config_metadata():
    from yonyou_doc2skill.cli.profile_detection import ProfileDecision
    from yonyou_doc2skill.cli.doc_scraper import DocToSkillConverter

    converter = DocToSkillConverter(
        {"name": "react", "base_url": "https://react.dev", "selectors": {"main_content": "article"}},
        dry_run=True,
    )
    converter._detected_profile = ProfileDecision("reference", 0.82, ["reference", "api"])

    metadata = converter._profile_metadata()
    assert metadata["suggested_profile"] == "reference"
    assert metadata["profile_confidence"] == 0.82
```

- [ ] **Step 2: Run the metadata tests to verify they fail**

Run: `pytest tests/test_profile_detection.py -q`
Expected: FAIL because `_profile_metadata()` does not exist.

- [ ] **Step 3: Add profile metadata helpers**

```python
def _profile_metadata(self) -> dict[str, object]:
    decision = getattr(self, "_detected_profile", None)
    return {
        "skill_profile": self._resolve_skill_profile(),
        "suggested_profile": getattr(decision, "profile", None),
        "profile_confidence": getattr(decision, "confidence", None),
        "profile_reasons": getattr(decision, "reasons", []),
    }
```

```python
# in save_summary()
summary.update(self._profile_metadata())
```

- [ ] **Step 4: Run the metadata tests to verify they pass**

Run: `pytest tests/test_profile_detection.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yonyou_doc2skill/cli/doc_scraper.py src/yonyou_doc2skill/cli/create_command.py tests/test_profile_detection.py
git commit -m "feat record detected skill profile metadata"
```

### Task 4: Update the Official Wrapper Skill to Ask or Pass Through Profile

**Files:**
- Modify: `skills/yonyou-doc2skill/SKILL.md`
- Modify: `skills/yonyou-doc2skill/scripts/run.py`
- Test: `tests/test_embedded_skill_runtime.py`
- Test: `tests/test_package_structure.py`

- [ ] **Step 1: Write the failing wrapper behavior tests**

```python
def test_skill_wrapper_docs_include_profile_guidance(repo_skill_dir):
    skill_md = (repo_skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "--profile" in skill_md
    assert "auto-detect" in skill_md.lower()
```

```python
def test_run_script_passes_profile_argument_through(tmp_path, monkeypatch, repo_skill_dir):
    run = load_script_module(repo_skill_dir / "scripts" / "run.py", "embedded_run_profile")
    captured = {}
    monkeypatch.setattr(run, "_execute_command", lambda argv: captured.setdefault("argv", argv) or 0)
    monkeypatch.setattr(run.bootstrap, "is_initialized", lambda: True)
    result = run.main(["create", "https://react.dev", "--profile", "reference"])
    assert result == 0
    assert "--profile" in captured["argv"]
```

- [ ] **Step 2: Run the wrapper tests to verify they fail**

Run: `pytest tests/test_embedded_skill_runtime.py tests/test_package_structure.py -q`
Expected: FAIL because wrapper docs do not mention profile handling.

- [ ] **Step 3: Update the wrapper instructions**

```markdown
## Profile Selection

- pass `--profile` when the user clearly wants a tutorial, reference, builder, troubleshooting, or internal-wiki skill
- if the user only provides a source, allow Doc2Skill to auto-detect the profile
- if the source purpose is still unclear and the runtime reports a low-confidence suggestion, ask the user whether they want a tutorial or reference style skill before re-running
```

```markdown
python3 scripts/run.py create https://docs.example.com --name my-docs-skill --profile reference --enhance-level 0
```

- [ ] **Step 4: Run the wrapper tests to verify they pass**

Run: `pytest tests/test_embedded_skill_runtime.py tests/test_package_structure.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/yonyou-doc2skill/SKILL.md tests/test_embedded_skill_runtime.py tests/test_package_structure.py
git commit -m "feat document profile-aware wrapper behavior"
```

### Task 5: Final Regression and Manual Smoke

**Files:**
- Modify: none expected
- Test: `tests/test_profile_detection.py`
- Test: `tests/test_profile_templates.py`
- Test: `tests/test_scraper_features.py`
- Test: `tests/test_embedded_skill_runtime.py`
- Test: `tests/test_package_structure.py`
- Test: `tests/test_cli_parsers.py`

- [ ] **Step 1: Run the focused regression suite**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_profile_detection.py \
  tests/test_profile_templates.py \
  tests/test_scraper_features.py \
  tests/test_embedded_skill_runtime.py \
  tests/test_package_structure.py \
  tests/test_cli_parsers.py -q
```

Expected: PASS

- [ ] **Step 2: Run one manual CLI smoke with explicit profile**

Run:

```bash
.venv/bin/yonyou-doc2skill create /Users/yonyou/sandbox/yonyou_doc2skill/tmp_gfwiki_22539572.html --name smoke-profile-reference --profile reference --enhance-level 0
```

Expected: `output/smoke-profile-reference/SKILL.md` exists and includes reference-oriented sections.

- [ ] **Step 3: Run one manual embedded-skill smoke without explicit profile**

Run:

```bash
cd skills/yonyou-doc2skill
python3 scripts/run.py create /Users/yonyou/sandbox/yonyou_doc2skill/tmp_gfwiki_22539572.html --name smoke-profile-auto --enhance-level 0
```

Expected: output exists under `skills/yonyou-doc2skill/output/smoke-profile-auto/` and summary metadata records an auto-detected profile.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat add profile-aware skill generation flow"
```
