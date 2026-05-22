import json
from argparse import Namespace
from pathlib import Path

from PIL import Image, ImageDraw

from yonyou_doc2skill.cli.sanitize_command import ImageSanitizer, TextSanitizer, sanitize_skill


def test_sanitize_text_replaces_sensitive_content(tmp_path):
    skill_dir = tmp_path / "skill"
    refs_dir = skill_dir / "references"
    refs_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "联系人 13812345678，邮箱 user@example.com，token: abcdefg",
        encoding="utf-8",
    )
    (refs_dir / "content.md").write_text("客户：某客户集团", encoding="utf-8")
    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace"},
                "custom_dictionaries": {"customer_name": ["某客户集团"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = sanitize_skill(
        Namespace(
            skill_directory=str(skill_dir),
            profile="delivery",
            config=str(config),
            images=False,
            images_only=False,
            image_mode="redact",
            ocr_engine="tesseract",
        )
    )

    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    ref_md = (refs_dir / "content.md").read_text(encoding="utf-8")
    report_json = json.loads((skill_dir / "sanitize/sanitize-report.json").read_text())

    assert "138****5678" in skill_md
    assert "us***@example.com" in skill_md
    assert "[ACCESS_TOKEN_REDACTED]" in skill_md
    assert "[CUSTOMER_NAME]" in ref_md
    assert report.files_modified == 2
    assert report_json["summary"]["findings"] >= 4


def test_sanitize_text_supports_custom_patterns_and_replacement_values(tmp_path):
    sanitizer = TextSanitizer.from_profile(
        "public",
        {
            "entities": {"project_name": "replace", "amount": "replace"},
            "custom_patterns": {"amount": r"\d+(?:\.\d+)?万元"},
            "replacement_values": {"project_name": "XX项目", "amount": "模拟金额"},
            "custom_dictionaries": {"project_name": ["华峰数智化BIP项目"]},
        },
    )

    sanitized, findings = sanitizer.sanitize("华峰数智化BIP项目 合同金额 1200.50万元")

    assert "XX项目" in sanitized
    assert "模拟金额" in sanitized
    assert "华峰" not in sanitized
    assert {item[0] for item in findings} == {"project_name", "amount"}


def test_image_redaction_writes_sanitized_copy_and_updates_markdown(tmp_path):
    skill_dir = tmp_path / "skill"
    assets_dir = skill_dir / "assets"
    refs_dir = skill_dir / "references"
    assets_dir.mkdir(parents=True)
    refs_dir.mkdir(parents=True)

    image_path = assets_dir / "screen.png"
    image = Image.new("RGB", (100, 50), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, 40, 30), fill="red")
    image.save(image_path)
    (refs_dir / "page.md").write_text("![screen](../assets/screen.png)", encoding="utf-8")

    sanitizer = ImageSanitizer(skill_dir, TextSanitizer.from_profile("public"), "redact")
    sanitizer._detect_boxes = lambda _path: ([(10, 10, 40, 30)], [])

    actions = sanitizer.sanitize_images()

    output_path = skill_dir / "assets_sanitized/screen.png"
    updated_md = (refs_dir / "page.md").read_text(encoding="utf-8")
    redacted = Image.open(output_path)

    assert output_path.exists()
    assert "assets_sanitized/screen.png" in updated_md
    assert redacted.getpixel((20, 20)) == (0, 0, 0)
    assert any(action.action_type == "image_redact" for action in actions)


def test_sanitize_images_without_optional_detectors_reports_warnings(tmp_path):
    skill_dir = tmp_path / "skill"
    assets_dir = skill_dir / "assets"
    assets_dir.mkdir(parents=True)
    Image.new("RGB", (10, 10), "white").save(assets_dir / "empty.png")

    report = sanitize_skill(
        Namespace(
            skill_directory=str(skill_dir),
            profile="delivery",
            config=None,
            images=True,
            images_only=True,
            image_mode="scan",
            ocr_engine="tesseract",
        )
    )

    assert (skill_dir / "sanitize/sanitize-report.json").exists()
    assert report.image_enabled is True


def test_image_sanitizer_accepts_ocr_engine_argument(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    sanitizer = ImageSanitizer(
        skill_dir,
        TextSanitizer.from_profile("public"),
        "scan",
        ocr_engine="tesseract",
    )

    assert sanitizer.ocr_engine == "tesseract"


def test_image_sanitizer_auto_ocr_falls_back_to_available_engine(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    sanitizer = ImageSanitizer(
        skill_dir,
        TextSanitizer.from_profile("public"),
        "scan",
        ocr_engine="auto",
    )

    assert sanitizer.ocr_engine in {"rapidocr", "paddleocr", "tesseract"}


def test_image_sanitizer_routes_ocr_detection_to_rapidocr(monkeypatch, tmp_path):
    skill_dir = tmp_path / "skill"
    assets_dir = skill_dir / "assets"
    assets_dir.mkdir(parents=True)
    image_path = assets_dir / "screen.png"
    Image.new("RGB", (40, 20), "white").save(image_path)

    sanitizer = ImageSanitizer(
        skill_dir,
        TextSanitizer.from_profile("public"),
        "scan",
        ocr_engine="rapidocr",
    )

    monkeypatch.setattr(
        sanitizer,
        "_detect_rapidocr_boxes",
        lambda _path: ([(1, 2, 3, 4)], True),
    )

    boxes, actions = sanitizer._detect_boxes(image_path)

    assert boxes == [(1, 2, 3, 4)]
    assert any(action.action_type == "ocr_text" for action in actions)


def test_image_sanitizer_routes_ocr_detection_to_paddleocr(monkeypatch, tmp_path):
    skill_dir = tmp_path / "skill"
    assets_dir = skill_dir / "assets"
    assets_dir.mkdir(parents=True)
    image_path = assets_dir / "screen.png"
    Image.new("RGB", (40, 20), "white").save(image_path)

    sanitizer = ImageSanitizer(
        skill_dir,
        TextSanitizer.from_profile("public"),
        "scan",
        ocr_engine="paddleocr",
    )

    monkeypatch.setattr(
        sanitizer,
        "_detect_paddleocr_boxes",
        lambda _path: ([(5, 6, 7, 8)], True),
    )

    boxes, actions = sanitizer._detect_boxes(image_path)

    assert boxes == [(5, 6, 7, 8)]
    assert any(action.action_type == "ocr_text" for action in actions)
