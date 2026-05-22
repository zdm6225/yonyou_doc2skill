"""Tests for enhance prepare mode bundle generation."""

from __future__ import annotations

import json
from pathlib import Path


def _make_skill_dir(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: demo\n---\n\n# Demo Skill\n", encoding="utf-8"
    )
    references_dir = skill_dir / "references" / "documentation"
    references_dir.mkdir(parents=True)
    (references_dir / "app.md").write_text(
        "# App Router\n\nUse `generateMetadata` for SEO.\n\n```ts\nexport default function Page() {}\n```\n",
        encoding="utf-8",
    )
    return skill_dir


def test_prepare_bundle_contains_expected_files(tmp_path):
    from yonyou_doc2skill.cli.enhance_prepare import generate_enhancement_bundle

    skill_dir = _make_skill_dir(tmp_path)
    bundle_dir = generate_enhancement_bundle(skill_dir, intent="给 Codex 做 reference skill")

    expected = {
        "manifest.json",
        "enhance-brief.md",
        "reference-map.md",
        "high-value-examples.md",
        "discrepancies.md",
        "rewrite-outline.md",
        "prompt.md",
        "status.json",
    }
    assert expected.issubset({path.name for path in bundle_dir.iterdir()})

    status = json.loads((bundle_dir / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "prepared"
    assert status["intent"] == "给 Codex 做 reference skill"


def test_prepare_bundle_does_not_modify_skill_md(tmp_path):
    from yonyou_doc2skill.cli.enhance_prepare import generate_enhancement_bundle

    skill_dir = _make_skill_dir(tmp_path)
    original = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    generate_enhancement_bundle(skill_dir)

    assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == original
