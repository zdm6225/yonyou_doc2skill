from argparse import Namespace
import json
import tempfile
from pathlib import Path


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
    from yonyou_doc2skill.cli.create_command import CreateCommand

    args = Namespace(source="https://react.dev", profile="reference", description=None)
    command = CreateCommand(args, parser_defaults={"profile": None})
    command.source_info = type(
        "S",
        (),
        {
            "type": "web",
            "raw_input": "https://react.dev",
            "suggested_name": "react",
            "parsed": {"url": "https://react.dev"},
        },
    )()

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


def _make_profile_decision(profile: str, confidence: float, reasons: list[str]) -> object:
    return type(
        "ProfileDecision",
        (),
        {"profile": profile, "confidence": confidence, "reasons": reasons},
    )()


def test_auto_detected_profile_is_recorded_in_config_metadata():
    from yonyou_doc2skill.cli.doc_scraper import DocToSkillConverter

    converter = DocToSkillConverter(
        {"name": "react", "base_url": "https://react.dev", "selectors": {"main_content": "article"}},
        dry_run=True,
    )
    converter._detected_profile = _make_profile_decision("reference", 0.82, ["reference", "api"])

    metadata = converter._profile_metadata()

    assert metadata["skill_profile"] == "reference"
    assert metadata["suggested_profile"] == "reference"
    assert metadata["profile_confidence"] == 0.82
    assert metadata["profile_reasons"] == ["reference", "api"]


def test_save_summary_persists_profile_metadata():
    from yonyou_doc2skill.cli.doc_scraper import DocToSkillConverter

    converter = DocToSkillConverter(
        {"name": "react", "base_url": "https://react.dev", "selectors": {"main_content": "article"}},
        dry_run=True,
    )
    converter.pages = [{"title": "Intro", "url": "https://react.dev/intro"}]
    converter._detected_profile = _make_profile_decision("reference", 0.91, ["reference", "api"])

    with tempfile.TemporaryDirectory() as tmpdir:
        converter.data_dir = tmpdir
        converter.save_summary()

        summary_path = Path(tmpdir) / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["skill_profile"] == "reference"
    assert summary["suggested_profile"] == "reference"
    assert summary["profile_confidence"] == 0.91
    assert summary["profile_reasons"] == ["reference", "api"]


def test_doc_scraper_auto_detects_profile_from_page_signals():
    from yonyou_doc2skill.cli.doc_scraper import DocToSkillConverter

    converter = DocToSkillConverter(
        {"name": "react", "base_url": "https://react.dev", "selectors": {"main_content": "article"}},
        dry_run=True,
    )
    pages = [
        {
            "title": "API Reference",
            "headings": [{"text": "Hooks"}, {"text": "Component API"}],
        }
    ]

    converter._detect_skill_profile_if_needed(pages)

    assert converter._detected_profile.profile == "reference"
    assert converter._resolve_skill_profile() == "reference"
