#!/usr/bin/env python3
"""Sanitize delivery asset packages before sharing or publishing."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import tempfile
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from yonyou_doc2skill.cli.sanitize_command import (
    IMAGE_EXTENSIONS,
    ImageAction,
    ImageSanitizer,
    ReplacementDetail,
    TextSanitizer,
    load_sanitize_config,
)

OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}
ARCHIVE_EXTENSIONS = {".zip"}
PDF_EXTENSIONS = {".pdf"}
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".csv", ".xml", ".yaml", ".yml"}
REVIEW_ONLY_EXTENSIONS = {".doc", ".vsdx"}
SKIP_NAMES = {".DS_Store", "Thumbs.db"}
VERIFY_SKIP_DIRS = {"sanitize-report"}
SCAN_TEXT_LIMIT_PER_FILE = 200_000
DEFAULT_LOGO_THRESHOLD = 0.88


INDUSTRY_REPLACEMENTS: dict[str, dict[str, str]] = {
    "general": {
        "customer_name": "某客户",
        "project_name": "XX项目",
        "person_name": "项目成员",
        "department_name": "某部门",
        "system_name": "某业务系统",
        "address": "某项目地址",
        "amount": "模拟金额",
        "ratio": "模拟比例",
    },
    "manufacturing": {
        "customer_name": "某制造集团",
        "project_name": "XX数智化项目",
        "person_name": "项目成员",
        "department_name": "某业务部门",
        "system_name": "某业务系统",
        "address": "某项目地址",
        "amount": "模拟金额",
        "ratio": "模拟比例",
    },
    "textile": {
        "customer_name": "某纺织集团",
        "project_name": "XX数智化BIP项目",
        "person_name": "项目成员",
        "department_name": "某业务部门",
        "system_name": "某业务系统",
        "address": "某项目地址",
        "amount": "模拟金额",
        "ratio": "模拟比例",
    },
}

BASE_ENTITIES: dict[str, str] = {
    "customer_name": "replace",
    "project_name": "replace",
    "person_name": "replace",
    "department_name": "replace",
    "system_name": "replace",
    "address": "replace",
    "amount": "replace",
    "ratio": "replace",
    "bank_account": "redact",
    "unified_social_credit_code": "redact",
}

BASE_PATTERNS: dict[str, str] = {
    "amount": r"(?<![A-Za-z0-9])\d+(?:\.\d+)?\s*(?:万元|亿元|元|万|亿)(?![A-Za-z0-9])",
    "ratio": r"\d+(?:\.\d+)?%",
    "address": r"[\u4e00-\u9fa5]{2,}(?:省|市|区|县|园区|街道|路|号)",
}

DEFAULT_ALLOWLIST = ["用友", "YonBIP", "BIP", "U8", "NC", "NCC", "ERP"]
SCAN_STOPWORDS = {
    "项目",
    "采集",
    "由技术",
    "由实施",
    "制定企业",
    "不良项目",
    "本次系统",
}
SANITIZE_INIT_PROMPT_TEMPLATE = """【资料脱敏初始化】

输入文件：
{input_path}

推荐选择：1 + 1 + 1
推荐说明：先做文本脱敏，快速拿到可信清单；确认无误后，再补跑 OCR 或 Logo。

一、脱敏清单生成方式

1. 规则扫描 + Agent 复核（推荐）
   适合：大多数交付资料
   速度：100MB Office 资料约 1-5 分钟
   开销：Agent 复核约 5k-20k tokens

2. 完全 Agent 扫描清单
   适合：文件少、语义复杂、需要强判断
   速度：单个 1-5MB 文件通常数分钟
   开销：大目录可能超过 100k tokens

3. 人工配置脱敏清单
   适合：正式交付前、强可控场景
   速度：最快
   开销：几乎不消耗额外模型 token

二、图片文字脱敏

1. 不开启图片文字脱敏（推荐）
   说明：只处理 Office / PDF 可提取文本、文件名和结构化内容
   优点：快，适合先验证规则

2. 开启 OCR 图片文字脱敏
   说明：处理截图、扫描件、扫描版 PDF、Office 内嵌图片文字
   提示：图片越多越慢，几十张通常 5-15 分钟，上千张可能 30 分钟以上

三、Logo 脱敏

1. 不开启 Logo 脱敏（推荐）
   说明：先不处理客户 Logo，避免额外扫描耗时

2. 开启 Logo 脱敏
   说明：需要提供 Logo 模板图
   用途：扫描 Word / PPT / PDF / 图片中的客户 Logo

补充规则：
- 如果第一项选择 3，则只表示“脱敏清单由人工配置”。
- 第二项、第三项仍严格按本轮选择执行，不会因为选择 3 而被重置。

直接回复以下任一格式即可

`选择：1 + 1 + 1`

如果要 Logo：

`选择：1 + 1 + 2`
`Logo 模板：/path/to/logo.png`

如果要正式完整脱敏：

`选择：1 + 2 + 2`
`Logo 模板：/path/to/logo.png`
"""
SANITIZE_MANUAL_PAGE_TEMPLATE = """【人工配置脱敏清单】

输入文件：
{input_path}

本轮选择：
- 脱敏清单方式：人工配置
- 图片文字脱敏：{image_mode_label}
- Logo 脱敏：{logo_mode_label}

填写说明：
- 这一步只负责人工确认业务词典，不会重置图片文字脱敏和 Logo 脱敏。
- 你只需要补充真实业务词、希望替换成什么，以及需要保留的白名单。
- 填完后直接使用同目录下的 `sanitize-config.reviewed.json` 执行 `apply` 和 `verify`。

建议优先补这几类：
- 客户名称：全称、简称、集团名、子公司名
- 项目名称：正式项目名、简称、一期/二期名
- 人员姓名：客户方、实施方、顾问、接口人
- 部门名称：事业部、财务部、供应链部、项目组
- 系统名称：业务系统、平台、中台、门户、接口名

你可以直接在配置文件里填写，也可以按下面格式回给 Agent：

客户名称：
- 原文 -> 替换文案

项目名称：
- 原文 -> 替换文案

人员姓名：
- 原文 -> 替换文案

部门名称：
- 原文 -> 替换文案

系统名称：
- 原文 -> 替换文案

白名单：
- 用友
- YonBIP

执行提示：
- 如果图片文字脱敏已开启，后续 `apply/verify` 会自动走 OCR。
- 如果 Logo 脱敏已开启但还没有模板图，请补一张 Logo 图路径，再执行 `logo-scan` 或在 `apply` 时附带 logo 配置。
"""


@dataclass
class AssetFinding:
    file: str
    entity: str
    action: str
    count: int
    location: str


@dataclass
class ReviewItem:
    file: str
    reason: str
    detail: str = ""


@dataclass
class RenameItem:
    source: str
    target: str


@dataclass
class ProcessedFile:
    source: str
    target: str
    file_type: str
    action: str


@dataclass
class AssetReplacementDetail:
    file: str
    location: str
    entity: str
    action: str
    original: str
    replacement: str
    start: int
    end: int


@dataclass
class LogoMatch:
    id: str
    file: str
    location: str
    box: list[int]
    confidence: float
    template: str
    preview: str = ""


@dataclass
class SanitizeAssetsReport:
    timestamp: str
    input_path: str
    output_path: str
    profile: str
    files_scanned: int = 0
    files_written: int = 0
    files_renamed: int = 0
    processed_files: list[ProcessedFile] = field(default_factory=list)
    renamed_items: list[RenameItem] = field(default_factory=list)
    findings: list[AssetFinding] = field(default_factory=list)
    replacement_details: list[AssetReplacementDetail] = field(default_factory=list)
    image_actions: list[ImageAction] = field(default_factory=list)
    review_items: list[ReviewItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DeliveryAssetScanner:
    """Generate project-specific sanitize config candidates."""

    def __init__(self, input_path: Path, output_path: Path, industry: str):
        self.input_path = input_path
        self.output_path = output_path
        self.industry = industry if industry in INDUSTRY_REPLACEMENTS else "general"
        self.file_type_counts: Counter[str] = Counter()
        self.media_count = 0
        self.review_items: list[ReviewItem] = []
        self.candidates: dict[str, Counter[str]] = {
            "customer_name": Counter(),
            "project_name": Counter(),
            "person_name": Counter(),
            "department_name": Counter(),
            "system_name": Counter(),
        }

    def run(self) -> dict[str, Any]:
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input path not found: {self.input_path}")
        if self.output_path.exists() and any(self.output_path.iterdir()):
            raise FileExistsError(f"Output directory is not empty: {self.output_path}")
        self.output_path.mkdir(parents=True, exist_ok=True)

        paths = [self.input_path] if self.input_path.is_file() else sorted(self.input_path.rglob("*"))
        for path in paths:
            if not path.is_file() or path.name in SKIP_NAMES:
                continue
            self._scan_file(path)

        config = self._build_config()
        report = self._build_report(config)
        (self.output_path / "sanitize-config.suggested.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (self.output_path / "sanitize-candidates.md").write_text(report, encoding="utf-8")
        return {
            "config_path": str(self.output_path / "sanitize-config.suggested.json"),
            "report_path": str(self.output_path / "sanitize-candidates.md"),
            "file_type_counts": dict(self.file_type_counts),
        }

    def _scan_file(self, path: Path) -> None:
        suffix = path.suffix.lower().lstrip(".") or "unknown"
        self.file_type_counts[suffix] += 1
        text_parts = [self._relative(path)]
        if path.suffix.lower() in OFFICE_EXTENSIONS:
            text, media_count = self._extract_ooxml_text(path)
            self.media_count += media_count
            text_parts.append(text[:SCAN_TEXT_LIMIT_PER_FILE])
        elif path.suffix.lower() in TEXT_EXTENSIONS:
            text_parts.append(path.read_text(encoding="utf-8", errors="ignore")[:SCAN_TEXT_LIMIT_PER_FILE])
        elif path.suffix.lower() in ARCHIVE_EXTENSIONS:
            text_parts.append(self._scan_zip_names(path))
        elif path.suffix.lower() in PDF_EXTENSIONS:
            text_parts.append(self._extract_pdf_text(path)[:SCAN_TEXT_LIMIT_PER_FILE])
        elif path.suffix.lower() in REVIEW_ONLY_EXTENSIONS:
            self.review_items.append(ReviewItem(file=self._relative(path), reason="unsupported_binary_format"))
        text = "\n".join(part for part in text_parts if part)
        self._collect_candidates(text)

    def _extract_ooxml_text(self, path: Path) -> tuple[str, int]:
        text_parts: list[str] = []
        media_count = 0
        try:
            with zipfile.ZipFile(path) as zf:
                for name in zf.namelist():
                    lower = name.lower()
                    if "/media/" in lower:
                        media_count += 1
                    if lower.endswith(".xml") and lower.startswith(("word/", "ppt/", "xl/", "docprops/")):
                        text_parts.append(zf.read(name).decode("utf-8", errors="ignore"))
        except zipfile.BadZipFile:
            self.review_items.append(ReviewItem(file=self._relative(path), reason="invalid_office_package"))
        return "\n".join(text_parts), media_count

    def _scan_zip_names(self, path: Path) -> str:
        try:
            with zipfile.ZipFile(path) as zf:
                return "\n".join(zf.namelist()[:1000])
        except zipfile.BadZipFile:
            self.review_items.append(ReviewItem(file=self._relative(path), reason="invalid_zip_package"))
            return ""

    def _extract_pdf_text(self, path: Path) -> str:
        try:
            import fitz
        except ImportError:
            self.review_items.append(ReviewItem(file=self._relative(path), reason="pdf_dependency_missing"))
            return ""

        try:
            with fitz.open(path) as doc:
                return "\n".join(page.get_text("text") for page in doc)
        except Exception as exc:
            self.review_items.append(
                ReviewItem(file=self._relative(path), reason="pdf_parse_failed", detail=str(exc))
            )
            return ""

    def _collect_candidates(self, text: str) -> None:
        for value in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+(?:数智化)?BIP项目", text):
            self._add_candidate("project_name", value)
        for value in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+项目", text):
            if 3 <= len(value) <= 30:
                self._add_candidate("project_name", value)
        for value in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+(?:集团|公司|企业|客户)", text):
            if 2 <= len(value) <= 24:
                self._add_candidate("customer_name", value)
        for value in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+(?:事业部|开发部|财务部|采购部|供应链|部门)", text):
            if 2 <= len(value) <= 24:
                self._add_candidate("department_name", value)
        for value in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+(?:系统|平台|门户|中台|接口|服务)", text):
            if 2 <= len(value) <= 24:
                self._add_candidate("system_name", value)
        for value in re.findall(r"[\u4e00-\u9fa5]{2,4}(?=(?:负责人|经理|顾问|总监|部长|主任))", text):
            self._add_candidate("person_name", value)

    def _add_candidate(self, entity: str, value: str) -> None:
        cleaned = value.strip(" _-【】[]（）()：:")
        if not cleaned or cleaned in DEFAULT_ALLOWLIST or cleaned in SCAN_STOPWORDS:
            return
        if "用友" in cleaned:
            return
        if entity in {"system_name", "customer_name", "project_name"} and len(cleaned) > 18:
            return
        if entity == "person_name" and not (2 <= len(cleaned) <= 4):
            return
        self.candidates[entity][cleaned] += 1

    def _build_config(self) -> dict[str, Any]:
        dictionaries = {
            entity: [value for value, _ in counter.most_common(50)]
            for entity, counter in self.candidates.items()
            if counter
        }
        return {
            "entities": BASE_ENTITIES,
            "replacement_values": INDUSTRY_REPLACEMENTS[self.industry],
            "custom_dictionaries": dictionaries,
            "custom_patterns": BASE_PATTERNS,
            "allowlist": DEFAULT_ALLOWLIST,
        }

    def _build_report(self, config: dict[str, Any]) -> str:
        lines = [
            "# 交付资产脱敏候选配置",
            "",
            f"- 输入：`{self.input_path}`",
            f"- 输出：`{self.output_path}`",
            f"- 行业模板：`{self.industry}`",
            f"- 内嵌媒体数量：{self.media_count}",
            "",
            "## 文件类型统计",
            "",
        ]
        for file_type, count in sorted(self.file_type_counts.items()):
            lines.append(f"- `{file_type}`：{count}")
        lines.extend(["", "## 默认替换文案", ""])
        for entity, value in config["replacement_values"].items():
            lines.append(f"- `{entity}` -> `{value}`")
        lines.extend(["", "## 候选词典", ""])
        dictionaries = config.get("custom_dictionaries") or {}
        if dictionaries:
            for entity, values in dictionaries.items():
                preview = "、".join(values[:30])
                lines.append(f"- `{entity}`：{preview}")
        else:
            lines.append("- 未发现候选词")
        lines.extend(["", "## 需要复核", ""])
        if self.review_items:
            for item in self.review_items[:200]:
                lines.append(f"- `{item.file}`：{item.reason}")
        else:
            lines.append("- 无")
        lines.extend(
            [
                "",
                "## 下一步",
                "",
                "1. 打开 `sanitize-config.suggested.json`，确认候选词和默认替换文案。",
                "2. 删除误识别词，补充客户简称、项目简称、人员姓名、系统名。",
                "3. 执行 `sanitize-assets apply` 生成脱敏资产包。",
            ]
        )
        return "\n".join(lines) + "\n"

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.input_path))
        except ValueError:
            return str(path)


def build_sanitize_init_prompt(input_path: Path | str) -> str:
    """Build the fixed sanitize initialization panel shown before any sanitization run."""
    return SANITIZE_INIT_PROMPT_TEMPLATE.format(input_path=Path(input_path))


def parse_sanitize_selection(selection: str) -> tuple[int, int, int]:
    """Parse a selection string like '3 + 2 + 1'."""
    normalized = selection.replace("选择：", "").replace("选择:", "").replace(" ", "")
    parts = normalized.split("+")
    if len(parts) != 3 or any(part not in {"1", "2", "3"} for part in parts[:1]) or any(
        part not in {"1", "2"} for part in parts[1:]
    ):
        raise ValueError("Invalid selection. Use forms like '1 + 1 + 1' or '3 + 2 + 2'.")
    return int(parts[0]), int(parts[1]), int(parts[2])


def build_manual_reviewed_config(
    input_path: Path,
    industry: str,
    image_mode: int,
    logo_mode: int,
    logo_template_path: str | None = None,
) -> dict[str, Any]:
    """Build a reviewed config template for manual-mode sanitization."""
    image_enabled = image_mode == 2
    logo_enabled = logo_mode == 2
    return {
        "_meta": {
            "input_path": str(input_path),
            "manual_mode": True,
            "selection": {
                "config_mode": 3,
                "image_mode": image_mode,
                "logo_mode": logo_mode,
            },
            "image_ocr_enabled": image_enabled,
            "logo_enabled": logo_enabled,
            "logo_template_path": logo_template_path or "",
        },
        "entities": BASE_ENTITIES,
        "replacement_values": INDUSTRY_REPLACEMENTS[industry if industry in INDUSTRY_REPLACEMENTS else "general"],
        "custom_dictionaries": {
            "customer_name": [],
            "project_name": [],
            "person_name": [],
            "department_name": [],
            "system_name": [],
        },
        "custom_patterns": BASE_PATTERNS,
        "allowlist": DEFAULT_ALLOWLIST,
    }


def build_manual_config_page(
    input_path: Path,
    image_mode: int,
    logo_mode: int,
) -> str:
    """Build the dedicated manual configuration page for selection mode 3."""
    image_mode_label = "开启 OCR" if image_mode == 2 else "不开启"
    logo_mode_label = "开启" if logo_mode == 2 else "不开启"
    return SANITIZE_MANUAL_PAGE_TEMPLATE.format(
        input_path=input_path,
        image_mode_label=image_mode_label,
        logo_mode_label=logo_mode_label,
    )


class LogoTemplateMatcher:
    """Find logo-like regions by matching user-provided logo templates."""

    def __init__(
        self,
        templates: list[Path],
        threshold: float,
        output_path: Path,
        mode: str = "redact",
        placeholder_text: str = "客户 LOGO",
    ):
        self.templates = templates
        self.threshold = threshold
        self.output_path = output_path
        self.mode = mode
        self.placeholder_text = placeholder_text
        self.matches: list[LogoMatch] = []
        self.review_items: list[ReviewItem] = []
        self._seen_office_candidates: set[tuple[str, str]] = set()

    def run(self, input_path: Path) -> dict[str, Any]:
        if not input_path.exists():
            raise FileNotFoundError(f"Input path not found: {input_path}")
        if self.output_path.exists() and any(self.output_path.iterdir()):
            raise FileExistsError(f"Output directory is not empty: {self.output_path}")
        self.output_path.mkdir(parents=True, exist_ok=True)

        paths = [input_path] if input_path.is_file() else sorted(input_path.rglob("*"))
        for path in paths:
            if not path.is_file() or path.name in SKIP_NAMES:
                continue
            self._scan_file(input_path, path)

        config = self._build_config()
        (self.output_path / "logo-config.suggested.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (self.output_path / "logo-review.md").write_text(
            self._render_review(input_path),
            encoding="utf-8",
        )
        return {
            "matches": len(self.matches),
            "config_path": str(self.output_path / "logo-config.suggested.json"),
            "review_path": str(self.output_path / "logo-review.md"),
        }

    def _scan_file(self, root: Path, path: Path) -> None:
        suffix = path.suffix.lower()
        rel = self._relative(root, path)
        if suffix in IMAGE_EXTENSIONS:
            self._scan_image_bytes(path.read_bytes(), suffix, rel, "image")
        elif suffix in OFFICE_EXTENSIONS:
            self._scan_office(root, path)
        elif suffix in PDF_EXTENSIONS:
            self._scan_pdf(root, path)

    def _scan_office(self, root: Path, path: Path) -> None:
        try:
            with zipfile.ZipFile(path) as zf:
                office_image_names = {
                    name
                    for name in zf.namelist()
                    if PurePosixPath(name).suffix.lower() in IMAGE_EXTENSIONS
                }
                office_links = self._extract_office_image_locations(zf)
                for name in zf.namelist():
                    suffix = PurePosixPath(name).suffix.lower()
                    if suffix in IMAGE_EXTENSIONS:
                        for location in office_links.get(name, []):
                            self._record_office_candidate(root, path, location, name)
                        self._scan_image_bytes(
                            zf.read(name),
                            suffix,
                            self._relative(root, path),
                            self._preferred_office_location(name, office_links, office_image_names),
                        )
        except zipfile.BadZipFile:
            self.review_items.append(ReviewItem(self._relative(root, path), "invalid_office_package"))

    def _scan_pdf(self, root: Path, path: Path) -> None:
        try:
            import fitz
        except ImportError:
            self.review_items.append(ReviewItem(self._relative(root, path), "pdf_dependency_missing"))
            return
        try:
            with fitz.open(path) as doc:
                for page_index, page in enumerate(doc):
                    pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
                    self._scan_image_bytes(
                        pix.tobytes("png"),
                        ".png",
                        self._relative(root, path),
                        f"pdf:page{page_index + 1}",
                    )
        except Exception as exc:
            self.review_items.append(ReviewItem(self._relative(root, path), "pdf_logo_scan_failed", str(exc)))

    def _scan_image_bytes(self, data: bytes, suffix: str, file: str, location: str) -> None:
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Logo scan requires opencv-python-headless and numpy.") from exc

        image_array = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            self.review_items.append(ReviewItem(file, "image_decode_failed", location))
            return
        for template_path in self.templates:
            template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
            if template is None:
                self.review_items.append(ReviewItem(str(template_path), "logo_template_decode_failed"))
                continue
            match = self._match_template(image, template)
            if not match:
                continue
            confidence, box = match
            match_id = f"L-{len(self.matches) + 1:04d}"
            preview = self._write_preview(match_id, image, box, suffix)
            self.matches.append(
                LogoMatch(
                    id=match_id,
                    file=file,
                    location=location,
                    box=box,
                    confidence=round(confidence, 4),
                    template=str(template_path),
                    preview=preview,
                )
            )

    def _match_template(self, image: Any, template: Any) -> tuple[float, list[int]] | None:
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Logo scan requires opencv-python-headless.") from exc

        best_match: tuple[float, list[int]] | None = None
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        base_h, base_w = template.shape[:2]

        for scale in (0.6, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5):
            scaled_w = max(1, int(round(base_w * scale)))
            scaled_h = max(1, int(round(base_h * scale)))
            if scaled_h > image.shape[0] or scaled_w > image.shape[1]:
                continue
            scaled = cv2.resize(template, (scaled_w, scaled_h), interpolation=cv2.INTER_LINEAR)
            scaled_gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)

            for candidate in (scaled, scaled_gray):
                target = image if candidate.ndim == 3 else image_gray
                result = cv2.matchTemplate(target, candidate, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val < self.threshold:
                    continue
                x, y = max_loc
                h, w = candidate.shape[:2]
                box = [int(x), int(y), int(x + w), int(y + h)]
                if best_match is None or max_val > best_match[0]:
                    best_match = (float(max_val), box)

        return best_match

    def _extract_office_image_locations(self, zf: zipfile.ZipFile) -> dict[str, list[str]]:
        office_links: dict[str, list[str]] = {}
        rel_files = [
            name
            for name in zf.namelist()
            if name.startswith(("word/_rels/", "ppt/_rels/", "xl/_rels/")) and name.endswith(".rels")
        ]

        for rel_name in rel_files:
            try:
                xml_text = zf.read(rel_name).decode("utf-8", errors="ignore")
            except KeyError:
                continue

            container_name = rel_name.replace("/_rels/", "/").removesuffix(".rels")
            location_prefix = "office"
            lower_container = container_name.lower()
            if "header" in lower_container:
                location_prefix = "office_header_candidate"
            elif "footer" in lower_container:
                location_prefix = "office_footer_candidate"
            elif "/slides/" in lower_container:
                location_prefix = "office_slide_candidate"

            for target in re.findall(r'Target="([^"]+)"', xml_text):
                resolved = self._resolve_office_relationship_target(container_name, target)
                if PurePosixPath(resolved).suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                office_links.setdefault(resolved, []).append(f"{location_prefix}:{resolved}")
        return office_links

    def _resolve_office_relationship_target(self, container_name: str, target: str) -> str:
        container = PurePosixPath(container_name)
        if target.startswith("/"):
            return target.lstrip("/")
        return str((container.parent / target).as_posix())

    def _preferred_office_location(
        self, image_name: str, office_links: dict[str, list[str]], office_image_names: set[str]
    ) -> str:
        linked_locations = office_links.get(image_name) or []
        for location in linked_locations:
            if location.startswith("office_header_candidate:"):
                return location
        for location in linked_locations:
            if location.startswith("office_footer_candidate:"):
                return location
        if image_name in office_image_names:
            return f"office:{image_name}"
        return "office"

    def _record_office_candidate(self, root: Path, path: Path, location: str, image_name: str) -> None:
        key = (self._relative(root, path), f"{location} {image_name}")
        if key in self._seen_office_candidates:
            return
        self._seen_office_candidates.add(key)
        self.review_items.append(
            ReviewItem(
                file=self._relative(root, path),
                reason=location.split(":", 1)[0],
                detail=image_name,
            )
        )

    def _write_preview(self, match_id: str, image: Any, box: list[int], suffix: str) -> str:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("Logo scan requires opencv-python-headless.") from exc

        preview_dir = self.output_path / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        x1, y1, x2, y2 = box
        preview = image.copy()
        cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 0, 255), 2)
        preview_name = f"{match_id}{suffix if suffix in IMAGE_EXTENSIONS else '.png'}"
        preview_path = preview_dir / preview_name
        cv2.imwrite(str(preview_path), preview)
        return str(preview_path.relative_to(self.output_path))

    def _build_config(self) -> dict[str, Any]:
        return {
            "logo_redaction": {
                "mode": self.mode,
                "placeholder_text": self.placeholder_text,
                "matches": [asdict(match) for match in self.matches],
            }
        }

    def _render_review(self, input_path: Path) -> str:
        lines = [
            "# Logo 脱敏候选报告",
            "",
            f"- 输入：`{input_path}`",
            f"- 输出：`{self.output_path}`",
            f"- 阈值：{self.threshold}",
            f"- 候选数量：{len(self.matches)}",
            "",
            "## 候选区域",
            "",
        ]
        if self.matches:
            for match in self.matches:
                lines.append(
                    f"- `{match.id}`：`{match.file}` `{match.location}` "
                    f"box={match.box} confidence={match.confidence} preview=`{match.preview}`"
                )
        else:
            lines.append("- 无")
        lines.extend(["", "## 需要复核", ""])
        if self.review_items:
            for item in self.review_items:
                lines.append(f"- `{item.file}`：{item.reason} {item.detail}".rstrip())
        else:
            lines.append("- 无")
        lines.extend(
            [
                "",
                "## 下一步",
                "",
                "1. 打开预览图确认候选区域是否为客户 Logo。",
                "2. 从 `logo-config.suggested.json` 删除误命中的 matches。",
                "3. 执行 `sanitize-assets apply ... --logo-config logo-config.suggested.json`。",
            ]
        )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _relative(root: Path, path: Path) -> str:
        if root.is_file():
            return path.name if path == root else path.name
        try:
            return str(path.relative_to(root))
        except ValueError:
            return path.name


class LogoRedactor:
    """Apply confirmed logo matches to image bytes."""

    def __init__(self, matches: list[LogoMatch], mode: str, placeholder_text: str):
        self.matches = matches
        self.mode = mode
        self.placeholder_text = placeholder_text

    @classmethod
    def from_config(cls, config: dict[str, Any] | None) -> "LogoRedactor | None":
        logo_config = (config or {}).get("logo_redaction") or {}
        matches = [
            LogoMatch(
                id=str(item.get("id") or f"L-{index + 1:04d}"),
                file=str(item.get("file") or ""),
                location=str(item.get("location") or "image"),
                box=[int(value) for value in item.get("box", [])],
                confidence=float(item.get("confidence") or 0),
                template=str(item.get("template") or ""),
                preview=str(item.get("preview") or ""),
            )
            for index, item in enumerate(logo_config.get("matches") or [])
            if len(item.get("box", [])) == 4
        ]
        if not matches:
            return None
        return cls(
            matches=matches,
            mode=logo_config.get("mode") or "placeholder",
            placeholder_text=logo_config.get("placeholder_text") or "客户 LOGO",
        )

    def matches_for(self, file: str, location: str) -> list[LogoMatch]:
        location_aliases = {location}
        if ":" in location:
            _, suffix = location.split(":", 1)
            location_aliases.update(
                {
                    f"office_header_candidate:{suffix}",
                    f"office_footer_candidate:{suffix}",
                    f"office_slide_candidate:{suffix}",
                    f"office:{suffix}",
                }
            )
        return [
            match
            for match in self.matches
            if match.file == file and (match.location in location_aliases or match.location == "image")
        ]

    def redact_image_bytes(self, data: bytes, suffix: str, matches: list[LogoMatch]) -> bytes:
        from io import BytesIO

        from PIL import Image, ImageDraw, ImageFont

        image = Image.open(BytesIO(data)).convert("RGB")
        draw = ImageDraw.Draw(image)
        for match in matches:
            x1, y1, x2, y2 = match.box
            if self.mode == "redact":
                draw.rectangle((x1, y1, x2, y2), fill="black")
                continue
            draw.rectangle((x1, y1, x2, y2), fill="white", outline="black", width=2)
            try:
                font = ImageFont.load_default()
                draw.text((x1 + 4, y1 + 4), self.placeholder_text, fill="black", font=font)
            except Exception:
                draw.text((x1 + 4, y1 + 4), self.placeholder_text, fill="black")
        output = BytesIO()
        fmt = "PNG" if suffix.lower() in {".png", ".webp"} else "JPEG"
        image.save(output, format=fmt)
        return output.getvalue()


class DeliveryAssetSanitizer:
    """Directory-level sanitizer for Office-heavy delivery assets."""

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        text_sanitizer: TextSanitizer,
        profile: str,
        image_mode: str,
        process_images: bool,
        ocr_engine: str = "auto",
        logo_config: dict[str, Any] | None = None,
        audit_detail: bool = False,
        audit_include_original: bool = False,
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.text_sanitizer = text_sanitizer
        self.profile = profile
        self.image_mode = image_mode
        self.process_images = process_images
        self.ocr_engine = ocr_engine
        self.logo_redactor = LogoRedactor.from_config(logo_config)
        self.audit_detail = audit_detail
        self.audit_include_original = audit_include_original
        self.report = SanitizeAssetsReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            input_path=str(input_path),
            output_path=str(output_path),
            profile=profile,
        )

    def run(self) -> SanitizeAssetsReport:
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input path not found: {self.input_path}")
        if self.output_path.exists() and any(self.output_path.iterdir()):
            raise FileExistsError(f"Output directory is not empty: {self.output_path}")
        self.output_path.mkdir(parents=True, exist_ok=True)

        if self.input_path.is_file():
            self._process_file(self.input_path, self.output_path / self._sanitize_name(self.input_path.name))
        else:
            self._process_directory(self.input_path, self.output_path)

        self._write_reports()
        return self.report

    def _process_directory(self, source_dir: Path, target_dir: Path) -> None:
        for source in sorted(source_dir.iterdir()):
            if source.name in SKIP_NAMES:
                continue
            target_name = self._sanitize_name(source.name)
            target = target_dir / target_name
            if target_name != source.name:
                self.report.files_renamed += 1
                self.report.renamed_items.append(
                    RenameItem(
                        source=str(source.relative_to(self.input_path)),
                        target=str(target.relative_to(self.output_path)),
                    )
                )
                self._record_findings(str(source.relative_to(self.input_path)), "path", source.name)
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                self._process_directory(source, target)
            elif source.is_file():
                self._process_file(source, target)

    def _process_file(self, source: Path, target: Path) -> None:
        self.report.files_scanned += 1
        suffix = source.suffix.lower()
        target.parent.mkdir(parents=True, exist_ok=True)
        action = "copied"

        if source.name in SKIP_NAMES:
            return
        if suffix in OFFICE_EXTENSIONS:
            self._process_office_file(source, target)
            action = "office_sanitized"
        elif suffix in PDF_EXTENSIONS:
            self._process_pdf_file(source, target)
            action = "pdf_sanitized"
        elif suffix in ARCHIVE_EXTENSIONS:
            self._process_zip_file(source, target)
            action = "zip_sanitized"
        elif suffix in IMAGE_EXTENSIONS and (self.process_images or self.logo_redactor):
            self._process_image_file(source, target)
            action = "image_sanitized"
        elif suffix in TEXT_EXTENSIONS:
            self._process_text_file(source, target)
            action = "text_sanitized"
        else:
            shutil.copy2(source, target)
            if suffix in REVIEW_ONLY_EXTENSIONS:
                action = "copied_review_required"
                self.report.review_items.append(
                    ReviewItem(
                        file=self._display_path(target),
                        reason="unsupported_binary_format",
                        detail="Convert to docx/pdf/image or review manually before publishing.",
                    )
                )
        self.report.files_written += 1
        self.report.processed_files.append(
            ProcessedFile(
                source=self._source_display_path(source),
                target=self._display_path(target),
                file_type=suffix.lstrip(".") or "unknown",
                action=action,
            )
        )

    def _process_text_file(self, source: Path, target: Path) -> None:
        text = source.read_text(encoding="utf-8", errors="ignore")
        sanitized, findings, details = self.text_sanitizer.sanitize_with_details(text)
        target.write_text(sanitized, encoding="utf-8")
        self._append_findings(target, "text", findings)
        self._append_details(target, "text", details)

    def _process_office_file(self, source: Path, target: Path) -> None:
        try:
            with zipfile.ZipFile(source) as zin, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    out_name = self._sanitize_archive_name(item.filename)
                    suffix = PurePosixPath(item.filename).suffix.lower()
                    location = f"office:{item.filename}"

                    if item.is_dir():
                        zout.writestr(out_name, data)
                        continue
                    if self._is_office_xml(item.filename):
                        data = self._sanitize_bytes(data, target, location)
                    elif suffix in IMAGE_EXTENSIONS and self.process_images:
                        data = self._sanitize_image_bytes(data, suffix, target, location)
                    if suffix in IMAGE_EXTENSIONS:
                        data = self._apply_logo_redaction_bytes(
                            data,
                            suffix,
                            self._source_display_path(source),
                            location,
                            target,
                        )
                    zout.writestr(out_name, data)
        except zipfile.BadZipFile:
            shutil.copy2(source, target)
            self.report.review_items.append(
                ReviewItem(
                    file=self._display_path(target),
                    reason="invalid_office_package",
                    detail="File could not be opened as OOXML package.",
                )
            )

    def _process_zip_file(self, source: Path, target: Path) -> None:
        try:
            with zipfile.ZipFile(source) as zin, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    out_name = self._sanitize_archive_name(item.filename)
                    suffix = PurePosixPath(item.filename).suffix.lower()
                    location = f"zip:{item.filename}"

                    if item.is_dir():
                        zout.writestr(out_name, data)
                        continue
                    if suffix in OFFICE_EXTENSIONS:
                        data = self._sanitize_nested_office_bytes(data, suffix, target, location)
                    elif suffix in PDF_EXTENSIONS:
                        data = self._sanitize_nested_pdf_bytes(data, suffix, target, location)
                    elif suffix in ARCHIVE_EXTENSIONS:
                        data = self._sanitize_nested_zip_bytes(data, suffix, target, location)
                    elif suffix in TEXT_EXTENSIONS:
                        data = self._sanitize_bytes(data, target, location)
                    elif suffix in IMAGE_EXTENSIONS and self.process_images:
                        data = self._sanitize_image_bytes(data, suffix, target, location)
                    if suffix in IMAGE_EXTENSIONS:
                        data = self._apply_logo_redaction_bytes(
                            data,
                            suffix,
                            self._source_display_path(source),
                            location,
                            target,
                        )
                    elif suffix in REVIEW_ONLY_EXTENSIONS:
                        self.report.review_items.append(
                            ReviewItem(
                                file=f"{self._display_path(target)}!{item.filename}",
                                reason="unsupported_binary_format",
                            )
                        )
                    zout.writestr(out_name, data)
        except zipfile.BadZipFile:
            shutil.copy2(source, target)
            self.report.review_items.append(
                ReviewItem(file=self._display_path(target), reason="invalid_zip_package")
            )

    def _process_pdf_file(self, source: Path, target: Path) -> None:
        try:
            import fitz
        except ImportError:
            shutil.copy2(source, target)
            self.report.review_items.append(
                ReviewItem(
                    file=self._display_path(target),
                    reason="pdf_dependency_missing",
                    detail="Install PyMuPDF to redact PDF files.",
                )
            )
            return

        try:
            with fitz.open(source) as doc:
                for page_index, page in enumerate(doc):
                    text = page.get_text("text")
                    _, findings, details = self.text_sanitizer.sanitize_with_details(text)
                    self._append_findings(target, f"pdf:page{page_index + 1}", findings)
                    self._append_details(target, f"pdf:page{page_index + 1}", details)
                    for detail in details:
                        if not detail.original:
                            continue
                        rects = page.search_for(detail.original)
                        for rect in rects:
                            page.add_redact_annot(rect, fill=(0, 0, 0))
                    if details:
                        page.apply_redactions()
                    self._process_pdf_page_image_fallback(page, target, page_index)
                    if self.logo_redactor:
                        matches = self.logo_redactor.matches_for(
                            self._source_display_path(source),
                            f"pdf:page{page_index + 1}",
                        )
                        for match in matches:
                            page.add_redact_annot(fitz.Rect(match.box), fill=(0, 0, 0))
                            self.report.image_actions.append(
                                ImageAction(
                                    file=f"{self._display_path(target)}:pdf:page{page_index + 1}",
                                    output=self._display_path(target),
                                    action_type="logo_redact",
                                    mode=self.logo_redactor.mode,
                                    box=match.box,
                                    detail=match.id,
                                )
                            )
                        if matches:
                            page.apply_redactions()
                doc.save(target, garbage=4, deflate=True)
        except Exception as exc:
            shutil.copy2(source, target)
            self.report.review_items.append(
                ReviewItem(
                    file=self._display_path(target),
                    reason="pdf_redaction_failed",
                    detail=str(exc),
                )
            )

    def _process_pdf_page_image_fallback(self, page: Any, target: Path, page_index: int) -> None:
        if self.image_mode == "scan":
            return
        try:
            import fitz
        except ImportError:
            return

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            input_image = tmp_dir / f"page-{page_index + 1}.png"
            output_image = tmp_dir / f"page-{page_index + 1}-out.png"

            pix = page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)
            pix.save(str(input_image))

            image_sanitizer = ImageSanitizer(
                tmp_dir,
                self.text_sanitizer,
                self.image_mode,
                ocr_engine=self.ocr_engine,
            )
            boxes, actions = image_sanitizer._detect_boxes(input_image)
            self.report.warnings.extend(image_sanitizer.warnings)
            if not boxes:
                return

            for action in actions:
                action.file = f"{self._display_path(target)}:pdf-image:page{page_index + 1}"
            self.report.image_actions.extend(actions)
            image_sanitizer._redact_image(input_image, output_image, boxes)
            self.report.findings.append(
                AssetFinding(
                    file=self._display_path(target),
                    entity="image_sensitive_region",
                    action="review",
                    count=len(boxes),
                    location=f"pdf-image:page{page_index + 1}",
                )
            )
            self.report.image_actions.append(
                ImageAction(
                    file=f"{self._display_path(target)}:pdf-image:page{page_index + 1}",
                    output=self._display_path(target),
                    action_type="image_redact",
                    mode=self.image_mode,
                    detail=f"{len(boxes)} region(s)",
                )
            )
            page.add_redact_annot(page.rect, fill=(0, 0, 0))
            page.apply_redactions()
            page.insert_image(page.rect, filename=str(output_image))

    def _process_image_file(self, source: Path, target: Path) -> None:
        data = source.read_bytes()
        sanitized = self._sanitize_image_bytes(data, source.suffix.lower(), target, "image")
        sanitized = self._apply_logo_redaction_bytes(
            sanitized,
            source.suffix.lower(),
            self._source_display_path(source),
            "image",
            target,
        )
        target.write_bytes(sanitized)

    def _sanitize_nested_office_bytes(
        self, data: bytes, suffix: str, owner: Path, location: str
    ) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            src = tmp_dir / f"input{suffix}"
            dst = tmp_dir / f"output{suffix}"
            src.write_bytes(data)
            self._process_office_file(src, dst)
            return dst.read_bytes() if dst.exists() else data

    def _sanitize_nested_zip_bytes(self, data: bytes, suffix: str, owner: Path, location: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            src = tmp_dir / f"input{suffix}"
            dst = tmp_dir / f"output{suffix}"
            src.write_bytes(data)
            self._process_zip_file(src, dst)
            return dst.read_bytes() if dst.exists() else data

    def _sanitize_nested_pdf_bytes(self, data: bytes, suffix: str, owner: Path, location: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            src = tmp_dir / f"input{suffix}"
            dst = tmp_dir / f"output{suffix}"
            src.write_bytes(data)
            before_review_count = len(self.report.review_items)
            self._process_pdf_file(src, dst)
            for item in self.report.review_items[before_review_count:]:
                item.file = f"{self._display_path(owner)}!{location}"
            return dst.read_bytes() if dst.exists() else data

    def _sanitize_bytes(self, data: bytes, owner: Path, location: str) -> bytes:
        text = data.decode("utf-8", errors="ignore")
        sanitized, findings, details = self.text_sanitizer.sanitize_with_details(text)
        self._append_findings(owner, location, findings)
        self._append_details(owner, location, details)
        return sanitized.encode("utf-8") if findings else data

    def _sanitize_image_bytes(self, data: bytes, suffix: str, owner: Path, location: str) -> bytes:
        if self.image_mode == "scan":
            return data
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            assets = tmp_dir / "assets"
            assets.mkdir()
            input_image = assets / f"image{suffix or '.png'}"
            output_image = tmp_dir / "assets_sanitized" / input_image.name
            input_image.write_bytes(data)

            image_sanitizer = ImageSanitizer(
                tmp_dir,
                self.text_sanitizer,
                self.image_mode,
                ocr_engine=self.ocr_engine,
            )
            boxes, actions = image_sanitizer._detect_boxes(input_image)
            self.report.warnings.extend(image_sanitizer.warnings)
            for action in actions:
                action.file = f"{self._display_path(owner)}:{location}"
            self.report.image_actions.extend(actions)
            if not boxes:
                return data
            output_image.parent.mkdir(parents=True, exist_ok=True)
            image_sanitizer._redact_image(input_image, output_image, boxes)
            self.report.image_actions.append(
                ImageAction(
                    file=f"{self._display_path(owner)}:{location}",
                    output=self._display_path(owner),
                    action_type="image_redact",
                    mode=self.image_mode,
                    detail=f"{len(boxes)} region(s)",
                )
            )
            return output_image.read_bytes()

    def _apply_logo_redaction_bytes(
        self,
        data: bytes,
        suffix: str,
        source_file: str,
        location: str,
        owner: Path,
    ) -> bytes:
        if not self.logo_redactor:
            return data
        matches = self.logo_redactor.matches_for(source_file, location)
        if not matches:
            return data
        try:
            output = self.logo_redactor.redact_image_bytes(data, suffix, matches)
        except Exception as exc:
            self.report.review_items.append(
                ReviewItem(
                    file=f"{self._display_path(owner)}:{location}",
                    reason="logo_redaction_failed",
                    detail=str(exc),
                )
            )
            return data
        for match in matches:
            self.report.image_actions.append(
                ImageAction(
                    file=f"{self._display_path(owner)}:{location}",
                    output=self._display_path(owner),
                    action_type="logo_redact",
                    mode=self.logo_redactor.mode,
                    box=match.box,
                    detail=match.id,
                )
            )
        return output

    def _sanitize_name(self, name: str) -> str:
        sanitized, _ = self.text_sanitizer.sanitize(name)
        sanitized = sanitized.replace("/", "_").replace(":", "_")
        return sanitized

    def _sanitize_archive_name(self, name: str) -> str:
        parts = PurePosixPath(name).parts
        return str(PurePosixPath(*(self._sanitize_name(part) for part in parts)))

    def _record_findings(self, file: str, location: str, text: str) -> None:
        _, findings, details = self.text_sanitizer.sanitize_with_details(text)
        for entity, action, count in findings:
            self.report.findings.append(AssetFinding(file, entity, action, count, location))
        if self.audit_detail:
            for detail in details:
                self.report.replacement_details.append(self._asset_detail(file, location, detail))

    def _append_findings(
        self,
        path: Path,
        location: str,
        findings: list[tuple[str, str, int]],
    ) -> None:
        if not findings:
            return
        file = self._display_path(path)
        for entity, action, count in findings:
            self.report.findings.append(AssetFinding(file, entity, action, count, location))

    def _append_details(self, path: Path, location: str, details: list[ReplacementDetail]) -> None:
        if not self.audit_detail or not details:
            return
        file = self._display_path(path)
        for detail in details:
            self.report.replacement_details.append(self._asset_detail(file, location, detail))

    def _asset_detail(
        self,
        file: str,
        location: str,
        detail: ReplacementDetail,
    ) -> AssetReplacementDetail:
        original = detail.original if self.audit_include_original else self._mask_audit_value(detail.original)
        return AssetReplacementDetail(
            file=file,
            location=location,
            entity=detail.entity,
            action=detail.action,
            original=original,
            replacement=detail.replacement,
            start=detail.start,
            end=detail.end,
        )

    def _mask_audit_value(self, value: str) -> str:
        if len(value) <= 2:
            return "*" * len(value)
        if len(value) <= 6:
            return f"{value[0]}***{value[-1]}"
        return f"{value[:2]}***{value[-2:]}"

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.output_path))
        except ValueError:
            return str(path)

    def _source_display_path(self, path: Path) -> str:
        if self.input_path.is_file():
            return path.name
        try:
            return str(path.relative_to(self.input_path))
        except ValueError:
            return str(path)

    def _write_reports(self) -> None:
        report_dir = self.output_path / "sanitize-report"
        report_dir.mkdir(parents=True, exist_ok=True)
        report = asdict(self.report)
        report["summary"] = {
            "files_scanned": self.report.files_scanned,
            "files_written": self.report.files_written,
            "files_renamed": self.report.files_renamed,
            "findings": sum(item.count for item in self.report.findings),
            "replacement_details": len(self.report.replacement_details),
            "image_actions": len(self.report.image_actions),
            "review_items": len(self.report.review_items),
            "warnings": len(self.report.warnings),
        }
        (report_dir / "sanitize-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (report_dir / "sanitize-report.md").write_text(self._render_markdown_report(report), encoding="utf-8")
        with (report_dir / "review-list.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file", "reason", "detail"])
            for item in self.report.review_items:
                writer.writerow([item.file, item.reason, item.detail])
        if self.audit_detail:
            with (report_dir / "sanitize-detail.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["file", "location", "entity", "action", "original", "replacement", "start", "end"]
                )
                for item in self.report.replacement_details:
                    writer.writerow(
                        [
                            item.file,
                            item.location,
                            item.entity,
                            item.action,
                            item.original,
                            item.replacement,
                            item.start,
                            item.end,
                        ]
                    )

    def _render_markdown_report(self, report: dict[str, Any]) -> str:
        summary = report["summary"]
        entity_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        file_counts: dict[str, int] = {}
        file_details: dict[str, dict[str, int]] = {}
        location_counts: dict[str, int] = {}

        for item in self.report.findings:
            entity_counts[item.entity] = entity_counts.get(item.entity, 0) + item.count
            action_counts[item.action] = action_counts.get(item.action, 0) + item.count
            file_counts[item.file] = file_counts.get(item.file, 0) + item.count
            location_group = item.location.split(":", 1)[0]
            location_counts[location_group] = location_counts.get(location_group, 0) + item.count
            details = file_details.setdefault(item.file, {})
            details[item.entity] = details.get(item.entity, 0) + item.count

        file_type_counts: dict[str, int] = {}
        for item in self.report.processed_files:
            file_type_counts[item.file_type] = file_type_counts.get(item.file_type, 0) + 1

        lines = [
            "# 交付资产脱敏报告",
            "",
            "## 基本信息",
            "",
            f"- 输入：`{self.input_path}`",
            f"- 输出：`{self.output_path}`",
            f"- Profile：`{self.profile}`",
            f"- 生成时间：`{self.report.timestamp}`",
            "",
            "## 处理结果总结",
            "",
            f"- 扫描文件：{summary['files_scanned']}",
            f"- 输出文件：{summary['files_written']}",
            f"- 重命名：{summary['files_renamed']}",
            f"- 文本命中：{summary['findings']}",
            f"- 替换明细：{summary['replacement_details']}",
            f"- 图片动作：{summary['image_actions']}",
            f"- 复核项：{summary['review_items']}",
            f"- 警告：{summary['warnings']}",
            "",
            "## 文件类型统计",
            "",
        ]
        if file_type_counts:
            for file_type, count in sorted(file_type_counts.items()):
                lines.append(f"- `{file_type}`：{count}")
        else:
            lines.append("- 无")

        lines.extend(["", "## 替换类型汇总", ""])
        if entity_counts:
            for entity, count in sorted(entity_counts.items()):
                lines.append(f"- `{entity}`：{count}")
        else:
            lines.append("- 无")

        lines.extend(["", "## 处理动作汇总", ""])
        if action_counts:
            for action, count in sorted(action_counts.items()):
                lines.append(f"- `{action}`：{count}")
        else:
            lines.append("- 无")

        lines.extend(["", "## 命中位置汇总", ""])
        if location_counts:
            for location, count in sorted(location_counts.items()):
                lines.append(f"- `{location}`：{count}")
        else:
            lines.append("- 无")

        lines.extend(["", "## 文件重命名结果", ""])
        if self.report.renamed_items:
            for item in self.report.renamed_items[:200]:
                lines.append(f"- `{item.source}` -> `{item.target}`")
        else:
            lines.append("- 无")

        lines.extend(["", "## 按文件替换明细", ""])
        if file_details:
            for file, details in sorted(file_details.items()):
                detail_text = "，".join(f"{entity}: {count}" for entity, count in sorted(details.items()))
                lines.append(f"- `{file}`：{detail_text}")
        else:
            lines.append("- 无")

        lines.extend(["", "## 输出文件清单", ""])
        if self.report.processed_files:
            for item in self.report.processed_files[:300]:
                lines.append(
                    f"- `{item.target}`：来源 `{item.source}`，类型 `{item.file_type}`，动作 `{item.action}`"
                )
        else:
            lines.append("- 无")

        lines.extend(["", "## 图片处理明细", ""])
        if self.report.image_actions:
            for item in self.report.image_actions[:200]:
                box = f"，box={item.box}" if item.box else ""
                lines.append(
                    f"- `{item.file}`：{item.action_type}，模式 `{item.mode}`{box} {item.detail}".rstrip()
                )
        else:
            lines.append("- 无")

        lines.extend(["", "## 逐项替换明细", ""])
        if self.report.replacement_details:
            lines.append("> 默认遮蔽原始值；如使用 `--audit-include-original`，这里会包含完整替换前内容。")
            lines.append("")
            lines.append("| 文件 | 位置 | 类型 | 动作 | 替换前 | 替换后 | 区间 |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for item in self.report.replacement_details[:200]:
                lines.append(
                    f"| `{item.file}` | `{item.location}` | `{item.entity}` | `{item.action}` | "
                    f"`{self._escape_table(item.original)}` | `{self._escape_table(item.replacement)}` | "
                    f"{item.start}-{item.end} |"
                )
            if len(self.report.replacement_details) > 200:
                lines.append("")
                lines.append("> 仅展示前 200 条，完整明细见 `sanitize-report/sanitize-detail.csv`。")
        elif self.audit_detail:
            lines.append("- 无")
        else:
            lines.append("- 未启用。需要逐项替换明细时，运行时增加 `--audit-detail`。")

        lines.extend(["", "## 复核项", ""])
        if self.report.review_items:
            for item in self.report.review_items[:200]:
                lines.append(f"- `{item.file}`：{item.reason} {item.detail}".rstrip())
        else:
            lines.append("- 无")

        lines.extend(["", "## 警告", ""])
        if self.report.warnings:
            for warning in sorted(set(self.report.warnings))[:200]:
                lines.append(f"- {warning}")
        else:
            lines.append("- 无")

        lines.extend(["", "## 后续建议", ""])
        if self.report.review_items:
            lines.append("- 先处理复核项中的旧版 Office、Visio 或无法解析文件，再对外发布。")
        if self.report.image_actions:
            lines.append("- 抽查已打码图片，确认遮盖区域不可逆且未遮挡必要业务说明。")
        if not self.report.review_items and not self.report.warnings:
            lines.append("- 本次未产生复核项和警告，可抽样检查后进入发布或归档流程。")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _escape_table(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", "\\n")

    @staticmethod
    def _is_office_xml(name: str) -> bool:
        lower = name.lower()
        return lower.endswith(".xml") and lower.startswith(("word/", "ppt/", "xl/", "docprops/"))


class DeliveryAssetVerifier:
    """Scan sanitized outputs for residual sensitive text."""

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        text_sanitizer: TextSanitizer,
        process_images: bool,
        ocr_engine: str = "auto",
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.text_sanitizer = text_sanitizer
        self.process_images = process_images
        self.ocr_engine = ocr_engine
        self.files_scanned = 0
        self.residuals: list[AssetFinding] = []
        self.review_items: list[ReviewItem] = []
        self.warnings: list[str] = []

    def run(self) -> dict[str, Any]:
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input path not found: {self.input_path}")
        if self.output_path.exists() and any(self.output_path.iterdir()):
            raise FileExistsError(f"Output directory is not empty: {self.output_path}")
        self.output_path.mkdir(parents=True, exist_ok=True)

        paths = [self.input_path] if self.input_path.is_file() else sorted(self.input_path.rglob("*"))
        for path in paths:
            if not path.is_file() or path.name in SKIP_NAMES:
                continue
            if any(part in VERIFY_SKIP_DIRS for part in path.relative_to(self.input_path).parts[:-1]):
                continue
            self.files_scanned += 1
            self._verify_file(path)

        report = self._build_report()
        (self.output_path / "verify-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (self.output_path / "verify-report.md").write_text(
            self._render_markdown_report(report),
            encoding="utf-8",
        )
        with (self.output_path / "verify-residuals.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file", "location", "entity", "action", "count"])
            for item in self.residuals:
                writer.writerow([item.file, item.location, item.entity, item.action, item.count])
        with (self.output_path / "verify-review-list.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file", "reason", "detail"])
            for item in self.review_items:
                writer.writerow([item.file, item.reason, item.detail])
        return report

    def _verify_file(self, path: Path) -> None:
        suffix = path.suffix.lower()
        if suffix in OFFICE_EXTENSIONS:
            self._verify_office(path)
        elif suffix in PDF_EXTENSIONS:
            self._verify_pdf(path)
        elif suffix in ARCHIVE_EXTENSIONS:
            self._verify_zip(path)
        elif suffix in TEXT_EXTENSIONS:
            self._verify_text(path, "text", path.read_text(encoding="utf-8", errors="ignore"))
        elif suffix in IMAGE_EXTENSIONS and self.process_images:
            self._verify_image(path)
        elif suffix in REVIEW_ONLY_EXTENSIONS:
            self.review_items.append(
                ReviewItem(file=self._relative(path), reason="unsupported_binary_format")
            )

    def _verify_text(self, path: Path, location: str, text: str) -> None:
        _, findings, _ = self.text_sanitizer.sanitize_with_details(text)
        self._append_residuals(self._relative(path), location, findings)

    def _verify_office(self, path: Path) -> None:
        try:
            with zipfile.ZipFile(path) as zf:
                for name in zf.namelist():
                    lower = name.lower()
                    if lower.endswith(".xml") and lower.startswith(("word/", "ppt/", "xl/", "docprops/")):
                        text = zf.read(name).decode("utf-8", errors="ignore")
                        self._verify_text(path, f"office:{name}", text)
        except zipfile.BadZipFile:
            self.review_items.append(ReviewItem(file=self._relative(path), reason="invalid_office_package"))

    def _verify_zip(self, path: Path) -> None:
        try:
            with zipfile.ZipFile(path) as zf:
                for item in zf.infolist():
                    if item.is_dir():
                        continue
                    name = item.filename
                    self._verify_text(path, f"zip-name:{name}", name)
                    suffix = PurePosixPath(name).suffix.lower()
                    if suffix in TEXT_EXTENSIONS:
                        text = zf.read(name).decode("utf-8", errors="ignore")
                        self._verify_text(path, f"zip:{name}", text)
                    elif suffix in REVIEW_ONLY_EXTENSIONS:
                        self.review_items.append(
                            ReviewItem(file=f"{self._relative(path)}!{name}", reason="unsupported_binary_format")
                        )
        except zipfile.BadZipFile:
            self.review_items.append(ReviewItem(file=self._relative(path), reason="invalid_zip_package"))

    def _verify_pdf(self, path: Path) -> None:
        try:
            import fitz
        except ImportError:
            self.review_items.append(ReviewItem(file=self._relative(path), reason="pdf_dependency_missing"))
            return

        try:
            with fitz.open(path) as doc:
                for page_index, page in enumerate(doc):
                    text = page.get_text("text")
                    self._verify_text(path, f"pdf:page{page_index + 1}", text)
                    if not text.strip():
                        self._verify_pdf_page_image(path, page, page_index)
        except Exception as exc:
            self.review_items.append(
                ReviewItem(file=self._relative(path), reason="pdf_parse_failed", detail=str(exc))
            )

    def _verify_pdf_page_image(self, path: Path, page: Any, page_index: int) -> None:
        try:
            import fitz
        except ImportError:
            return

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            image_path = tmp_dir / f"page-{page_index + 1}.png"
            pix = page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)
            pix.save(str(image_path))

            image_sanitizer = ImageSanitizer(
                tmp_dir,
                self.text_sanitizer,
                "scan",
                ocr_engine=self.ocr_engine,
            )
            boxes, _ = image_sanitizer._detect_boxes(image_path)
            self.warnings.extend(image_sanitizer.warnings)
            if boxes:
                self.residuals.append(
                    AssetFinding(
                        self._relative(path),
                        "image_sensitive_region",
                        "review",
                        len(boxes),
                        f"pdf-image:page{page_index + 1}",
                    )
                )

    def _verify_image(self, path: Path) -> None:
        image_sanitizer = ImageSanitizer(
            self.input_path if self.input_path.is_dir() else path.parent,
            self.text_sanitizer,
            "scan",
            ocr_engine=self.ocr_engine,
        )
        boxes, _ = image_sanitizer._detect_boxes(path)
        self.warnings.extend(image_sanitizer.warnings)
        if boxes:
            self.residuals.append(
                AssetFinding(self._relative(path), "image_sensitive_region", "review", len(boxes), "image")
            )

    def _append_residuals(
        self,
        file: str,
        location: str,
        findings: list[tuple[str, str, int]],
    ) -> None:
        for entity, action, count in findings:
            self.residuals.append(AssetFinding(file, entity, action, count, location))

    def _build_report(self) -> dict[str, Any]:
        residual_count = sum(item.count for item in self.residuals)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_path": str(self.input_path),
            "output_path": str(self.output_path),
            "passed": residual_count == 0 and not self.review_items,
            "summary": {
                "files_scanned": self.files_scanned,
                "residual_findings": residual_count,
                "residual_items": len(self.residuals),
                "review_items": len(self.review_items),
                "warnings": len(self.warnings),
            },
            "residuals": [asdict(item) for item in self.residuals],
            "review_items": [asdict(item) for item in self.review_items],
            "warnings": sorted(set(self.warnings)),
        }

    def _render_markdown_report(self, report: dict[str, Any]) -> str:
        summary = report["summary"]
        lines = [
            "# 脱敏残留复核报告",
            "",
            "## 基本信息",
            "",
            f"- 输入：`{self.input_path}`",
            f"- 输出：`{self.output_path}`",
            f"- 生成时间：`{report['timestamp']}`",
            f"- 复核结论：{'通过' if report['passed'] else '不通过'}",
            "",
            "## 结果汇总",
            "",
            f"- 扫描文件：{summary['files_scanned']}",
            f"- 残留命中：{summary['residual_findings']}",
            f"- 残留条目：{summary['residual_items']}",
            f"- 复核项：{summary['review_items']}",
            f"- 警告：{summary['warnings']}",
            "",
            "## 残留明细",
            "",
        ]
        if self.residuals:
            for item in self.residuals[:300]:
                lines.append(
                    f"- `{item.file}`：{item.location} 命中 `{item.entity}` "
                    f"{item.count} 处，建议动作 `{item.action}`"
                )
            if len(self.residuals) > 300:
                lines.append("")
                lines.append("> 仅展示前 300 条，完整明细见 `verify-residuals.csv`。")
        else:
            lines.append("- 无")

        lines.extend(["", "## 需要人工复核", ""])
        if self.review_items:
            for item in self.review_items[:300]:
                lines.append(f"- `{item.file}`：{item.reason} {item.detail}".rstrip())
        else:
            lines.append("- 无")

        lines.extend(["", "## 后续建议", ""])
        if self.residuals:
            lines.append("- 根据残留明细补充词典或规则后重新执行 `sanitize-assets apply`。")
        if self.review_items:
            lines.append("- 先处理无法自动解析的格式，再对外发布。")
        if not self.residuals and not self.review_items:
            lines.append("- 未发现配置范围内的残留敏感信息，可进入抽样人工验收。")
        return "\n".join(lines) + "\n"

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.input_path))
        except ValueError:
            return path.name


def sanitize_assets(args: argparse.Namespace) -> SanitizeAssetsReport:
    config = load_sanitize_config(args.config)
    if getattr(args, "logo_config", None):
        logo_config = load_sanitize_config(args.logo_config)
        config["logo_redaction"] = logo_config.get("logo_redaction") or logo_config
    text_sanitizer = TextSanitizer.from_profile(args.profile, config)
    sanitizer = DeliveryAssetSanitizer(
        input_path=Path(args.input_path),
        output_path=Path(args.output),
        text_sanitizer=text_sanitizer,
        profile=args.profile,
        image_mode=args.image_mode,
        process_images=not args.no_images,
        ocr_engine=args.ocr_engine,
        logo_config=config,
        audit_detail=args.audit_detail,
        audit_include_original=args.audit_include_original,
    )
    return sanitizer.run()


def verify_assets(args: argparse.Namespace) -> dict[str, Any]:
    config = load_sanitize_config(args.config)
    text_sanitizer = TextSanitizer.from_profile(args.profile, config)
    verifier = DeliveryAssetVerifier(
        input_path=Path(args.input_path),
        output_path=Path(args.output),
        text_sanitizer=text_sanitizer,
        process_images=not args.no_images,
        ocr_engine=args.ocr_engine,
    )
    return verifier.run()


def scan_assets(args: argparse.Namespace) -> dict[str, Any]:
    scanner = DeliveryAssetScanner(
        input_path=Path(args.input_path),
        output_path=Path(args.output),
        industry=args.industry,
    )
    return scanner.run()


def init_assets(args: argparse.Namespace) -> dict[str, Any]:
    prompt = build_sanitize_init_prompt(Path(args.input_path))
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    init_path = output_path / "sanitize-init.md"
    init_path.write_text(prompt, encoding="utf-8")
    result = {
        "prompt": prompt,
        "init_path": str(init_path),
    }
    selection = getattr(args, "selection", None)
    if selection:
        config_mode, image_mode, logo_mode = parse_sanitize_selection(selection)
        if config_mode == 3:
            manual_page = build_manual_config_page(Path(args.input_path), image_mode, logo_mode)
            manual_path = output_path / "sanitize-manual-config.md"
            manual_path.write_text(manual_page, encoding="utf-8")
            reviewed_config = build_manual_reviewed_config(
                input_path=Path(args.input_path),
                industry=args.industry,
                image_mode=image_mode,
                logo_mode=logo_mode,
                logo_template_path=getattr(args, "logo_template_path", None),
            )
            reviewed_path = output_path / "sanitize-config.reviewed.json"
            reviewed_path.write_text(
                json.dumps(reviewed_config, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result.update(
                {
                    "prompt": manual_page,
                    "manual_path": str(manual_path),
                    "reviewed_config_path": str(reviewed_path),
                }
            )
    return result


def logo_scan_assets(args: argparse.Namespace) -> dict[str, Any]:
    templates = [Path(path) for path in (args.logo_template or [])]
    if not templates:
        raise ValueError("--logo-template is required for sanitize-assets logo-scan")
    matcher = LogoTemplateMatcher(
        templates=templates,
        threshold=args.logo_threshold,
        output_path=Path(args.output),
        mode=args.logo_mode,
        placeholder_text=args.logo_placeholder_text,
    )
    return matcher.run(Path(args.input_path))


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "mode_or_input",
        help="Mode (init/scan/apply/verify/logo-scan) or delivery asset file/directory for backward-compatible apply",
    )
    parser.add_argument("input_path", nargs="?", help="Delivery asset file or directory")
    parser.add_argument("--output", "-o", required=True, help="Output directory for sanitized assets")
    parser.add_argument(
        "--profile",
        choices=["internal", "delivery", "public"],
        default="delivery",
        help="Sanitization profile",
    )
    parser.add_argument("--config", help="JSON/YAML sanitize config file")
    parser.add_argument(
        "--image-mode",
        choices=["blur", "pixelate", "redact", "scan"],
        default="redact",
        help="Image action for detected regions",
    )
    parser.add_argument(
        "--ocr-engine",
        choices=["auto", "rapidocr", "paddleocr", "tesseract"],
        default="auto",
        help="OCR backend for screenshot/image text detection",
    )
    parser.add_argument("--no-images", action="store_true", help="Skip embedded image redaction")
    parser.add_argument(
        "--industry",
        choices=sorted(INDUSTRY_REPLACEMENTS),
        default="general",
        help="Default replacement wording for generated scan config",
    )
    parser.add_argument(
        "--selection",
        help="Optional init selection such as '1 + 1 + 1' or '3 + 2 + 1'",
    )
    parser.add_argument(
        "--logo-template-path",
        help="Optional logo template path recorded when init selection enables logo redaction",
    )
    parser.add_argument(
        "--audit-detail",
        action="store_true",
        help="Record each replacement in Markdown and sanitize-detail.csv",
    )
    parser.add_argument(
        "--audit-include-original",
        action="store_true",
        help="Include original sensitive values in audit detail output",
    )
    parser.add_argument(
        "--logo-template",
        action="append",
        help="Logo template image for sanitize-assets logo-scan; can be repeated",
    )
    parser.add_argument("--logo-config", help="Confirmed logo redaction config from logo-scan")
    parser.add_argument(
        "--logo-threshold",
        type=float,
        default=DEFAULT_LOGO_THRESHOLD,
        help="Template match threshold for logo-scan",
    )
    parser.add_argument(
        "--logo-mode",
        choices=["redact", "placeholder"],
        default="redact",
        help="Logo redaction mode used in generated logo config",
    )
    parser.add_argument(
        "--logo-placeholder-text",
        default="客户 LOGO",
        help="Placeholder text used for logo replacement",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sanitize delivery asset packages")
    add_arguments(parser)
    return parser


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    if args.mode_or_input in {"init", "scan", "apply", "verify", "logo-scan"}:
        args.mode = args.mode_or_input
        if not args.input_path:
            raise ValueError(f"input_path is required for sanitize-assets {args.mode}")
    else:
        args.mode = "apply"
        if args.input_path:
            raise ValueError("Unexpected extra positional argument. Use 'scan <input>' or 'apply <input>'.")
        args.input_path = args.mode_or_input
    return args


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args = normalize_args(args)
        if args.mode == "init":
            result = init_assets(args)
            print(result["prompt"])
            print("")
            print(f"Init panel: {result['init_path']}")
            if result.get("manual_path"):
                print(f"Manual page: {result['manual_path']}")
            if result.get("reviewed_config_path"):
                print(f"Reviewed config: {result['reviewed_config_path']}")
            return 0
        if args.mode == "scan":
            result = scan_assets(args)
            print(f"Sanitize scan complete: {args.output}")
            print(f"Suggested config: {result['config_path']}")
            print(f"Candidate report: {result['report_path']}")
            return 0
        if args.mode == "logo-scan":
            result = logo_scan_assets(args)
            print(f"Logo scan complete: {args.output}")
            print(f"Matches: {result['matches']}")
            print(f"Logo config: {result['config_path']}")
            print(f"Review report: {result['review_path']}")
            return 0
        if args.mode == "verify":
            report = verify_assets(args)
            print(f"Sanitize verify complete: {args.output}")
            print(f"Files scanned: {report['summary']['files_scanned']}")
            print(f"Residual findings: {report['summary']['residual_findings']}")
            print(f"Review items: {report['summary']['review_items']}")
            print(f"Report: {Path(args.output) / 'verify-report.md'}")
            return 0 if report["passed"] else 2
        report = sanitize_assets(args)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    print(f"Sanitize assets complete: {report.output_path}")
    print(f"Files scanned: {report.files_scanned}")
    print(f"Files written: {report.files_written}")
    print(f"Findings: {sum(item.count for item in report.findings)}")
    print(f"Review items: {len(report.review_items)}")
    print(f"Report: {Path(report.output_path) / 'sanitize-report' / 'sanitize-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
