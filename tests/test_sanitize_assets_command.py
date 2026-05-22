import json
import zipfile
from argparse import Namespace
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from yonyou_doc2skill.cli.sanitize_assets_command import (
    build_sanitize_init_prompt,
    init_assets,
    logo_scan_assets,
    normalize_args,
    sanitize_assets,
    scan_assets,
    verify_assets,
)


def _write_ooxml(path: Path, xml_name: str, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr(xml_name, f"<root><t>{text}</t></root>")


def _run(input_path: Path, output: Path, config: Path | None = None):
    return sanitize_assets(
        Namespace(
            input_path=str(input_path),
            mode_or_input=str(input_path),
            output=str(output),
            profile="public",
            config=str(config) if config else None,
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            logo_config=None,
            logo_template=None,
            logo_threshold=0.9,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            ocr_engine="tesseract",
        )
    )


def _make_logo(path: Path, color: tuple[int, int, int] = (220, 20, 60)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (60, 30), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((5, 5, 55, 25), fill=color)
    draw.text((18, 10), "HF", fill="white")
    image.save(path)


def _make_image_with_logo(path: Path, logo_path: Path) -> None:
    canvas = Image.new("RGB", (220, 120), "white")
    logo = Image.open(logo_path).convert("RGB")
    canvas.paste(logo, (20, 20))
    canvas.save(path)


def _make_ooxml_with_header_logo(path: Path, logo_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    logo_bytes = logo_path.read_bytes()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<w:document/>")
        zf.writestr(
            "word/header2.xml",
            (
                '<w:hdr xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<w:p><w:r><w:drawing><a:blip r:embed="rId1"/></w:drawing></w:r></w:p></w:hdr>'
            ),
        )
        zf.writestr(
            "word/_rels/header2.xml.rels",
            (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                'Target="media/image1.png"/></Relationships>'
            ),
        )
        zf.writestr("word/media/image1.png", logo_bytes)


def test_sanitize_assets_sanitizes_office_text_and_paths(tmp_path):
    source = tmp_path / "福建华峰项目"
    output = tmp_path / "out"
    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace", "project_name": "replace"},
                "custom_dictionaries": {
                    "customer_name": ["华峰"],
                    "project_name": ["福建华峰项目"],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write_ooxml(
        source / "【华峰数智化BIP项目】方案.docx",
        "word/document.xml",
        "客户 华峰 联系人 13812345678 邮箱 user@example.com",
    )

    report = _run(source, output, config)

    files = list(output.rglob("*.docx"))
    assert files
    assert "华峰" not in str(files[0])
    with zipfile.ZipFile(files[0]) as zf:
        content = zf.read("word/document.xml").decode("utf-8")
    assert "[CUSTOMER_NAME]" in content
    assert "[PHONE_REDACTED]" in content
    assert "[EMAIL_REDACTED]" in content
    assert report.files_renamed >= 1
    assert (output / "sanitize-report/sanitize-report.json").exists()


def test_sanitize_assets_recurses_into_zip_packages(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    nested_doc = tmp_path / "nested.docx"
    _write_ooxml(nested_doc, "word/document.xml", "token: abcdefg")
    with zipfile.ZipFile(source / "资料.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(nested_doc, "nested.docx")

    output = tmp_path / "out"
    report = _run(source, output)

    out_zip = output / "资料.zip"
    assert out_zip.exists()
    with zipfile.ZipFile(out_zip) as zf:
        nested_bytes = zf.read("nested.docx")
    nested_out = tmp_path / "nested-out.docx"
    nested_out.write_bytes(nested_bytes)
    with zipfile.ZipFile(nested_out) as zf:
        content = zf.read("word/document.xml").decode("utf-8")
    assert "[ACCESS_TOKEN_REDACTED]" in content
    assert sum(item.count for item in report.findings) >= 1


def test_sanitize_assets_marks_unsupported_binary_for_review(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    (source / "legacy.doc").write_bytes(b"binary")

    output = tmp_path / "out"
    report = _run(source, output)

    assert (output / "legacy.doc").exists()
    assert report.review_items
    assert report.review_items[0].reason == "unsupported_binary_format"
    assert (output / "sanitize-report/review-list.csv").exists()


def test_sanitize_assets_audit_detail_records_each_replacement(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    (source / "note.txt").write_text("客户 华峰 手机 13812345678", encoding="utf-8")
    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace"},
                "custom_dictionaries": {"customer_name": ["华峰"]},
                "replacement_values": {"customer_name": "某纺织集团"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output = tmp_path / "out"

    report = sanitize_assets(
        Namespace(
            input_path=str(source),
            mode_or_input=str(source),
            output=str(output),
            profile="public",
            config=str(config),
            image_mode="scan",
            no_images=True,
            audit_detail=True,
            audit_include_original=False,
            ocr_engine="tesseract",
        )
    )

    detail_csv = output / "sanitize-report/sanitize-detail.csv"
    detail_md = (output / "sanitize-report/sanitize-report.md").read_text(encoding="utf-8")
    csv_text = detail_csv.read_text(encoding="utf-8")

    assert detail_csv.exists()
    assert len(report.replacement_details) == 2
    assert "逐项替换明细" in detail_md
    assert "华峰" not in csv_text
    assert "**" in csv_text
    assert "某纺织集团" in csv_text


def test_sanitize_assets_scan_generates_suggested_config(tmp_path):
    source = tmp_path / "福建华峰项目"
    _write_ooxml(
        source / "【华峰数智化BIP项目】方案.docx",
        "word/document.xml",
        "华峰数智化BIP项目 福建华峰集团 采购系统",
    )
    output = tmp_path / "scan"

    result = scan_assets(
        Namespace(
            input_path=str(source),
            output=str(output),
            industry="textile",
            ocr_engine="tesseract",
        )
    )

    config = json.loads((output / "sanitize-config.suggested.json").read_text(encoding="utf-8"))
    report = (output / "sanitize-candidates.md").read_text(encoding="utf-8")

    assert result["config_path"].endswith("sanitize-config.suggested.json")
    assert config["replacement_values"]["customer_name"] == "某纺织集团"
    assert "华峰数智化BIP项目" in config["custom_dictionaries"]["project_name"]
    assert "福建华峰集团" in config["custom_dictionaries"]["customer_name"]
    assert "候选词典" in report


def test_sanitize_assets_init_prompt_is_fixed_user_choice_panel(tmp_path):
    source = tmp_path / "福建华峰项目"
    source.mkdir()

    prompt = build_sanitize_init_prompt(source)

    assert "【资料脱敏初始化】" in prompt
    assert "输入文件：" in prompt
    assert "推荐选择：1 + 1 + 1" in prompt
    assert "一、脱敏清单生成方式" in prompt
    assert "二、图片文字脱敏" in prompt
    assert "三、Logo 脱敏" in prompt
    assert "直接回复以下任一格式即可" in prompt
    assert "如果第一项选择 3，则只表示“脱敏清单由人工配置”" in prompt
    assert "第二项、第三项仍严格按本轮选择执行" in prompt
    assert "选择：1 + 1 + 1" in prompt
    assert str(source) in prompt


def test_sanitize_assets_init_manual_selection_generates_manual_page_and_reviewed_config(tmp_path):
    source = tmp_path / "华峰方案.docx"
    source.write_text("dummy", encoding="utf-8")
    output = tmp_path / "init"

    result = init_assets(
        Namespace(
            input_path=str(source),
            output=str(output),
            industry="textile",
            selection="3 + 2 + 1",
            logo_template_path=None,
        )
    )

    manual_page = output / "sanitize-manual-config.md"
    reviewed_config = output / "sanitize-config.reviewed.json"

    assert result["prompt"].startswith("【人工配置脱敏清单】")
    assert result["manual_path"] == str(manual_page)
    assert result["reviewed_config_path"] == str(reviewed_config)
    assert "图片文字脱敏：开启 OCR" in manual_page.read_text(encoding="utf-8")
    assert "Logo 脱敏：不开启" in manual_page.read_text(encoding="utf-8")

    config = json.loads(reviewed_config.read_text(encoding="utf-8"))
    assert config["_meta"]["selection"] == {"config_mode": 3, "image_mode": 2, "logo_mode": 1}
    assert config["_meta"]["manual_mode"] is True
    assert config["replacement_values"]["project_name"] == "XX数智化BIP项目"
    assert "customer_name" in config["custom_dictionaries"]


def test_sanitize_assets_normalize_args_supports_scan_apply_and_legacy():
    legacy = normalize_args(
        Namespace(mode_or_input="/tmp/input", input_path=None, output="/tmp/out")
    )
    scan = normalize_args(
        Namespace(mode_or_input="scan", input_path="/tmp/input", output="/tmp/out")
    )
    apply = normalize_args(
        Namespace(mode_or_input="apply", input_path="/tmp/input", output="/tmp/out")
    )
    verify = normalize_args(
        Namespace(mode_or_input="verify", input_path="/tmp/input", output="/tmp/out")
    )
    logo_scan = normalize_args(
        Namespace(mode_or_input="logo-scan", input_path="/tmp/input", output="/tmp/out")
    )
    init = normalize_args(
        Namespace(mode_or_input="init", input_path="/tmp/input", output="/tmp/out")
    )

    assert legacy.mode == "apply"
    assert legacy.input_path == "/tmp/input"
    assert scan.mode == "scan"
    assert apply.mode == "apply"
    assert verify.mode == "verify"
    assert logo_scan.mode == "logo-scan"
    assert init.mode == "init"


def test_sanitize_assets_verify_reports_residual_findings(tmp_path):
    source = tmp_path / "out"
    source.mkdir()
    (source / "note.txt").write_text("客户 华峰 手机 13812345678", encoding="utf-8")
    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace", "phone": "redact"},
                "custom_dictionaries": {"customer_name": ["华峰"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = verify_assets(
        Namespace(
            input_path=str(source),
            mode_or_input="verify",
            output=str(tmp_path / "verify"),
            profile="public",
            config=str(config),
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    assert report["summary"]["residual_findings"] == 2
    assert report["passed"] is False
    assert (tmp_path / "verify/verify-report.md").exists()


def test_sanitize_assets_verify_ignores_sanitize_report_directory(tmp_path):
    source = tmp_path / "out"
    report_dir = source / "sanitize-report"
    report_dir.mkdir(parents=True)
    (report_dir / "sanitize-report.md").write_text("原始文件 华峰项目", encoding="utf-8")
    (source / "note.txt").write_text("客户 某纺织集团", encoding="utf-8")
    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace"},
                "custom_dictionaries": {"customer_name": ["华峰"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = verify_assets(
        Namespace(
            input_path=str(source),
            mode_or_input="verify",
            output=str(tmp_path / "verify"),
            profile="public",
            config=str(config),
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    assert report["summary"]["files_scanned"] == 1
    assert report["summary"]["residual_findings"] == 0
    assert report["passed"] is True


def test_sanitize_assets_verify_passes_when_no_residual_findings(tmp_path):
    source = tmp_path / "out"
    source.mkdir()
    (source / "note.txt").write_text("客户 某纺织集团 手机 [PHONE_REDACTED]", encoding="utf-8")

    report = verify_assets(
        Namespace(
            input_path=str(source),
            mode_or_input="verify",
            output=str(tmp_path / "verify"),
            profile="public",
            config=None,
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    assert report["summary"]["residual_findings"] == 0
    assert report["passed"] is True


def test_sanitize_assets_sanitizes_pdf_text(tmp_path):
    fitz = __import__("pytest").importorskip("fitz")
    source = tmp_path / "assets"
    source.mkdir()
    pdf_path = source / "方案.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "客户 华峰 联系电话 13812345678")
    doc.save(pdf_path)
    doc.close()

    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace", "phone": "redact"},
                "custom_dictionaries": {"customer_name": ["华峰"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output = tmp_path / "out"

    report = _run(source, output, config)

    out_pdf = output / "方案.pdf"
    assert out_pdf.exists()
    assert any(item.file == "方案.pdf" and item.entity == "phone" for item in report.findings)
    with fitz.open(out_pdf) as out_doc:
        text = "\n".join(page.get_text("text") for page in out_doc)
    assert "13812345678" not in text


def test_sanitize_assets_pdf_text_pages_do_not_use_ocr_fallback(monkeypatch, tmp_path):
    fitz = pytest.importorskip("fitz")
    source = tmp_path / "assets"
    source.mkdir()
    pdf_path = source / "方案.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "客户 华峰 联系电话 13812345678")
    doc.save(pdf_path)
    doc.close()

    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace", "phone": "redact"},
                "custom_dictionaries": {"customer_name": ["华峰"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("OCR fallback should not run for text PDFs")

    monkeypatch.setattr(
        "yonyou_doc2skill.cli.sanitize_command.ImageSanitizer._detect_boxes",
        fail_if_called,
    )

    report = _run(source, tmp_path / "out", config)

    assert any(item.location == "pdf:page1" for item in report.findings)
    assert not any(item.location == "pdf-image:page1" for item in report.findings)


def test_sanitize_assets_ocr_fallback_handles_scanned_pdf_pages(monkeypatch, tmp_path):
    fitz = pytest.importorskip("fitz")
    source = tmp_path / "assets"
    source.mkdir()
    pdf_path = source / "扫描方案.pdf"

    image = Image.new("RGB", (320, 120), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 30), "客户 华峰", fill="black")
    image_path = tmp_path / "scan.png"
    image.save(image_path)

    doc = fitz.open()
    page = doc.new_page(width=320, height=120)
    page.insert_image(page.rect, filename=str(image_path))
    doc.save(pdf_path)
    doc.close()

    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace"},
                "custom_dictionaries": {"customer_name": ["华峰"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "yonyou_doc2skill.cli.sanitize_command.ImageSanitizer._detect_boxes",
        lambda self, _path: (
            [(10, 10, 100, 60)],
            [],
        ),
    )

    report = sanitize_assets(
        Namespace(
            input_path=str(source),
            mode_or_input=str(source),
            output=str(tmp_path / "out"),
            profile="public",
            config=str(config),
            image_mode="redact",
            no_images=False,
            audit_detail=False,
            audit_include_original=False,
            logo_config=None,
            logo_template=None,
            logo_threshold=0.9,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            ocr_engine="tesseract",
        )
    )

    assert (tmp_path / "out/扫描方案.pdf").exists()
    assert any(item.location == "pdf-image:page1" for item in report.findings)
    assert any(action.action_type == "image_redact" for action in report.image_actions)


def test_sanitize_assets_verify_ocr_fallback_reports_scanned_pdf_residuals(monkeypatch, tmp_path):
    fitz = pytest.importorskip("fitz")
    source = tmp_path / "out"
    source.mkdir()
    pdf_path = source / "扫描方案.pdf"

    image = Image.new("RGB", (320, 120), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 30), "客户 华峰", fill="black")
    image_path = tmp_path / "scan.png"
    image.save(image_path)

    doc = fitz.open()
    page = doc.new_page(width=320, height=120)
    page.insert_image(page.rect, filename=str(image_path))
    doc.save(pdf_path)
    doc.close()

    config = tmp_path / "sanitize.json"
    config.write_text(
        json.dumps(
            {
                "entities": {"customer_name": "replace"},
                "custom_dictionaries": {"customer_name": ["华峰"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "yonyou_doc2skill.cli.sanitize_command.ImageSanitizer._detect_boxes",
        lambda self, _path: (
            [(10, 10, 100, 60)],
            [("ignored")],
        ),
    )

    report = verify_assets(
        Namespace(
            input_path=str(source),
            mode_or_input="verify",
            output=str(tmp_path / "verify"),
            profile="public",
            config=str(config),
            image_mode="scan",
            no_images=False,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    assert report["summary"]["residual_findings"] >= 1
    assert report["passed"] is False


def test_sanitize_assets_logo_scan_generates_candidates_and_config(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    logo = tmp_path / "logo.png"
    _make_logo(logo)
    _make_image_with_logo(source / "cover.png", logo)

    result = logo_scan_assets(
        Namespace(
            input_path=str(source),
            mode_or_input="logo-scan",
            output=str(tmp_path / "logo-scan"),
            logo_template=[str(logo)],
            logo_threshold=0.9,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            profile="public",
            config=None,
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    config = json.loads((tmp_path / "logo-scan/logo-config.suggested.json").read_text(encoding="utf-8"))
    review = (tmp_path / "logo-scan/logo-review.md").read_text(encoding="utf-8")

    assert result["matches"] == 1
    assert config["logo_redaction"]["mode"] == "redact"
    assert config["logo_redaction"]["matches"][0]["file"] == "cover.png"
    assert "cover.png" in review


def test_sanitize_assets_logo_scan_keeps_placeholder_as_optional_mode(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    logo = tmp_path / "logo.png"
    _make_logo(logo)
    _make_image_with_logo(source / "cover.png", logo)

    logo_scan_assets(
        Namespace(
            input_path=str(source),
            mode_or_input="logo-scan",
            output=str(tmp_path / "logo-scan"),
            logo_template=[str(logo)],
            logo_threshold=0.9,
            logo_mode="placeholder",
            logo_placeholder_text="客户 LOGO",
            profile="public",
            config=None,
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    config = json.loads((tmp_path / "logo-scan/logo-config.suggested.json").read_text(encoding="utf-8"))

    assert config["logo_redaction"]["mode"] == "placeholder"


def test_sanitize_assets_logo_scan_matches_scaled_template(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    logo = tmp_path / "logo.png"
    _make_logo(logo)

    scaled = tmp_path / "scaled-logo.png"
    Image.open(logo).resize((90, 45)).save(scaled)
    _make_image_with_logo(source / "cover.png", scaled)

    result = logo_scan_assets(
        Namespace(
            input_path=str(source),
            mode_or_input="logo-scan",
            output=str(tmp_path / "logo-scan"),
            logo_template=[str(logo)],
            logo_threshold=0.9,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            profile="public",
            config=None,
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    assert result["matches"] == 1


def test_sanitize_assets_logo_scan_reports_office_header_candidates_when_no_match(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    logo = tmp_path / "logo.png"
    _make_logo(logo)
    docx = source / "header-logo.docx"
    _make_ooxml_with_header_logo(docx, logo)

    unmatched_template = tmp_path / "other-logo.png"
    image = Image.new("RGB", (60, 30), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 4, 52, 26), fill=(0, 120, 255))
    draw.text((18, 8), "ZZ", fill="white")
    image.save(unmatched_template)

    result = logo_scan_assets(
        Namespace(
            input_path=str(source),
            mode_or_input="logo-scan",
            output=str(tmp_path / "logo-scan"),
            logo_template=[str(unmatched_template)],
            logo_threshold=0.95,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            profile="public",
            config=None,
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    review = (tmp_path / "logo-scan/logo-review.md").read_text(encoding="utf-8")

    assert result["matches"] == 0
    assert "office_header_candidate" in review
    assert "word/media/image1.png" in review


def test_sanitize_assets_logo_scan_single_file_uses_real_filename(tmp_path):
    logo = tmp_path / "logo.png"
    _make_logo(logo)
    docx = tmp_path / "header-logo.docx"
    _make_ooxml_with_header_logo(docx, logo)

    result = logo_scan_assets(
        Namespace(
            input_path=str(docx),
            mode_or_input="logo-scan",
            output=str(tmp_path / "logo-scan"),
            logo_template=[str(logo)],
            logo_threshold=0.88,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            profile="public",
            config=None,
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            industry="general",
            ocr_engine="tesseract",
        )
    )

    config = json.loads((tmp_path / "logo-scan/logo-config.suggested.json").read_text(encoding="utf-8"))

    assert result["matches"] == 1
    assert config["logo_redaction"]["matches"][0]["file"] == "header-logo.docx"


def test_sanitize_assets_apply_single_file_docx_uses_logo_match_filename(tmp_path):
    logo = tmp_path / "logo.png"
    _make_logo(logo)
    docx = tmp_path / "header-logo.docx"
    _make_ooxml_with_header_logo(docx, logo)
    logo_config = tmp_path / "logo-config.json"
    logo_config.write_text(
        json.dumps(
            {
                "logo_redaction": {
                    "mode": "redact",
                    "matches": [
                        {
                            "id": "L-0001",
                            "file": "header-logo.docx",
                            "location": "office_header_candidate:word/media/image1.png",
                            "box": [0, 0, 60, 30],
                            "confidence": 1.0,
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    base_config = tmp_path / "sanitize.json"
    base_config.write_text(
        json.dumps(
            {
                "entities": {},
                "custom_dictionaries": {},
                "replacement_values": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = sanitize_assets(
        Namespace(
            input_path=str(docx),
            mode_or_input=str(docx),
            output=str(tmp_path / "out"),
            profile="public",
            config=str(base_config),
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            logo_config=str(logo_config),
            logo_template=None,
            logo_threshold=0.9,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            ocr_engine="tesseract",
        )
    )

    assert any(action.action_type == "logo_redact" for action in report.image_actions)


def test_sanitize_assets_apply_uses_logo_config_for_images(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    logo = tmp_path / "logo.png"
    _make_logo(logo)
    _make_image_with_logo(source / "cover.png", logo)
    logo_config = tmp_path / "logo-config.json"
    logo_config.write_text(
        json.dumps(
            {
                "logo_redaction": {
                    "mode": "placeholder",
                    "placeholder_text": "客户 LOGO",
                    "matches": [
                        {
                            "id": "L-0001",
                            "file": "cover.png",
                            "location": "image",
                            "box": [20, 20, 80, 50],
                            "confidence": 1.0,
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = sanitize_assets(
        Namespace(
            input_path=str(source),
            mode_or_input=str(source),
            output=str(tmp_path / "out"),
            profile="public",
            config=None,
            image_mode="scan",
            no_images=False,
            audit_detail=False,
            audit_include_original=False,
            logo_config=str(logo_config),
            logo_template=None,
            logo_threshold=0.9,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            ocr_engine="tesseract",
        )
    )

    assert (tmp_path / "out/cover.png").exists()
    assert any(action.action_type == "logo_redact" for action in report.image_actions)
    out_image = Image.open(tmp_path / "out/cover.png").convert("RGB")
    assert out_image.getpixel((25, 25)) != Image.open(logo).convert("RGB").getpixel((5, 5))


def test_sanitize_assets_logo_config_still_applies_when_ocr_images_are_disabled(tmp_path):
    source = tmp_path / "assets"
    source.mkdir()
    logo = tmp_path / "logo.png"
    _make_logo(logo)
    _make_image_with_logo(source / "cover.png", logo)
    logo_config = tmp_path / "logo-config.json"
    logo_config.write_text(
        json.dumps(
            {
                "logo_redaction": {
                    "mode": "redact",
                    "matches": [
                        {
                            "id": "L-0001",
                            "file": "cover.png",
                            "location": "image",
                            "box": [20, 20, 80, 50],
                            "confidence": 1.0,
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = sanitize_assets(
        Namespace(
            input_path=str(source),
            mode_or_input=str(source),
            output=str(tmp_path / "out"),
            profile="public",
            config=None,
            image_mode="scan",
            no_images=True,
            audit_detail=False,
            audit_include_original=False,
            logo_config=str(logo_config),
            logo_template=None,
            logo_threshold=0.9,
            logo_mode="redact",
            logo_placeholder_text="客户 LOGO",
            ocr_engine="tesseract",
        )
    )

    assert any(action.action_type == "logo_redact" for action in report.image_actions)
