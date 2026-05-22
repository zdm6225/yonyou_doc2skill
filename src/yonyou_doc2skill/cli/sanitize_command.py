#!/usr/bin/env python3
"""Sanitize generated skills before sharing or packaging."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TEXT_PATTERNS: dict[str, re.Pattern[str]] = {
    "phone": re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "id_card": re.compile(r"(?<!\d)\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"),
    "unified_social_credit_code": re.compile(r"\b[0-9A-Z]{18}\b"),
    "bank_account": re.compile(r"(?<!\d)(?:\d[ -]?){16,24}(?!\d)"),
    "access_token": re.compile(
        r"(?i)\b(?:access[_-]?token|refresh[_-]?token|api[_-]?key|secret[_-]?key|"
        r"authorization|bearer|cookie|sessionid|jsessionid|yht_access_token|"
        r"token|key|secret|password)\b"
        r"\s*[:=]\s*['\"]?[^'\";\s]+"
    ),
    "internal_ip": re.compile(
        r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"
    ),
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


@dataclass
class Finding:
    file: str
    entity: str
    action: str
    count: int


@dataclass
class ReplacementDetail:
    entity: str
    action: str
    original: str
    replacement: str
    start: int
    end: int


@dataclass
class ImageAction:
    file: str
    output: str
    action_type: str
    mode: str
    box: list[int] | None = None
    detail: str = ""


@dataclass
class SanitizeReport:
    timestamp: str
    skill_directory: str
    profile: str
    text_enabled: bool
    image_enabled: bool
    files_scanned: int = 0
    files_modified: int = 0
    findings: list[Finding] = field(default_factory=list)
    image_actions: list[ImageAction] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class TextSanitizer:
    """Regex and dictionary based text sanitizer."""

    def __init__(
        self,
        entities: dict[str, str],
        custom_dictionaries: dict[str, list[str]] | None = None,
        allowlist: list[str] | None = None,
        replacement_values: dict[str, str] | None = None,
        custom_patterns: dict[str, re.Pattern[str]] | None = None,
    ):
        self.entities = entities
        self.custom_dictionaries = custom_dictionaries or {}
        self.allowlist = allowlist or []
        self.replacement_values = replacement_values or {}
        self.custom_patterns = custom_patterns or {}

    @classmethod
    def from_profile(cls, profile: str, config: dict[str, Any] | None = None) -> "TextSanitizer":
        config = config or {}
        defaults = {
            "internal": {
                "access_token": "redact",
                "email": "mask",
                "phone": "mask",
            },
            "delivery": {
                "access_token": "redact",
                "email": "mask",
                "phone": "mask",
                "id_card": "redact",
                "internal_ip": "replace",
                "bank_account": "redact",
                "unified_social_credit_code": "redact",
                "customer_name": "hash",
                "project_name": "replace",
            },
            "public": {
                "access_token": "redact",
                "email": "redact",
                "phone": "redact",
                "id_card": "redact",
                "internal_ip": "replace",
                "bank_account": "redact",
                "unified_social_credit_code": "redact",
                "customer_name": "hash",
                "project_name": "replace",
            },
        }
        entities = dict(defaults.get(profile, defaults["delivery"]))
        entities.update(config.get("entities") or {})
        custom_patterns = {
            name: re.compile(pattern)
            for name, pattern in (config.get("custom_patterns") or {}).items()
            if pattern
        }
        return cls(
            entities=entities,
            custom_dictionaries=config.get("custom_dictionaries") or {},
            allowlist=config.get("allowlist") or [],
            replacement_values=config.get("replacement_values") or {},
            custom_patterns=custom_patterns,
        )

    def sanitize(self, text: str) -> tuple[str, list[tuple[str, str, int]]]:
        result, findings, _ = self.sanitize_with_details(text)
        return result, findings

    def sanitize_with_details(
        self, text: str
    ) -> tuple[str, list[tuple[str, str, int]], list[ReplacementDetail]]:
        findings: list[tuple[str, str, int]] = []
        details: list[ReplacementDetail] = []
        result = text

        for entity, pattern in TEXT_PATTERNS.items():
            action = self.entities.get(entity)
            if not action or action == "off":
                continue
            result, count, replaced = self._sub_with_details(result, entity, action, pattern)
            details.extend(replaced)
            if count:
                findings.append((entity, action, count))

        for entity, pattern in self.custom_patterns.items():
            action = self.entities.get(entity, "replace")
            if action == "off":
                continue
            result, count, replaced = self._sub_with_details(result, entity, action, pattern)
            details.extend(replaced)
            if count:
                findings.append((entity, action, count))

        for entity, words in self.custom_dictionaries.items():
            action = self.entities.get(entity, "replace")
            if action == "off":
                continue
            for word in sorted(words, key=len, reverse=True):
                if not word or word in self.allowlist:
                    continue
                replacement = self._replacement(entity, action, word)
                result, count, replaced = self._sub_with_details(
                    result,
                    entity,
                    action,
                    re.compile(re.escape(word)),
                    fixed_replacement=replacement,
                )
                details.extend(replaced)
                if count:
                    findings.append((entity, action, count))

        return result, findings, details

    def _sub_with_details(
        self,
        text: str,
        entity: str,
        action: str,
        pattern: re.Pattern[str],
        fixed_replacement: str | None = None,
    ) -> tuple[str, int, list[ReplacementDetail]]:
        details: list[ReplacementDetail] = []
        parts: list[str] = []
        last_end = 0
        delta = 0
        for match in pattern.finditer(text):
            original = match.group(0)
            replacement = fixed_replacement or self._replacement(entity, action, original)
            parts.append(text[last_end : match.start()])
            parts.append(replacement)
            details.append(
                ReplacementDetail(
                    entity=entity,
                    action=action,
                    original=original,
                    replacement=replacement,
                    start=match.start() + delta,
                    end=match.start() + delta + len(replacement),
                )
            )
            delta += len(replacement) - (match.end() - match.start())
            last_end = match.end()
        if not details:
            return text, 0, []
        parts.append(text[last_end:])
        return "".join(parts), len(details), details

    def has_sensitive(self, text: str) -> bool:
        _, findings = self.sanitize(text)
        return bool(findings)

    def _replacement(self, entity: str, action: str, value: str) -> str:
        if any(allowed and allowed in value for allowed in self.allowlist):
            return value
        if action == "mask":
            return self._mask(entity, value)
        if action == "hash":
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
            return f"[{entity.upper()}_{digest}]"
        if action == "redact":
            return f"[{entity.upper()}_REDACTED]"
        return self.replacement_values.get(entity, f"[{entity.upper()}]")

    def _mask(self, entity: str, value: str) -> str:
        if entity == "phone":
            digits = re.sub(r"\D", "", value)
            if len(digits) >= 11:
                return f"{digits[:3]}****{digits[-4:]}"
        if entity == "email" and "@" in value:
            name, domain = value.split("@", 1)
            return f"{name[:2]}***@{domain}"
        return f"[{entity.upper()}_MASKED]"


class ImageSanitizer:
    """Image redaction with optional OCR, face, and QR detectors."""

    def __init__(
        self,
        skill_dir: Path,
        text_sanitizer: TextSanitizer,
        mode: str,
        ocr_engine: str = "auto",
    ):
        self.skill_dir = skill_dir
        self.text_sanitizer = text_sanitizer
        self.mode = mode
        self.requested_ocr_engine = ocr_engine
        self.ocr_engine = self._resolve_ocr_engine(ocr_engine)
        self.warnings: list[str] = []

    def sanitize_images(self) -> list[ImageAction]:
        actions: list[ImageAction] = []
        for image_path in self._iter_images():
            rel = image_path.relative_to(self.skill_dir)
            boxes, detector_actions = self._detect_boxes(image_path)
            actions.extend(detector_actions)

            if not boxes:
                continue

            if self.mode == "scan":
                continue

            output_path = self._sanitized_path(image_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self._redact_image(image_path, output_path, boxes)
            actions.append(
                ImageAction(
                    file=str(rel),
                    output=str(output_path.relative_to(self.skill_dir)),
                    action_type="image_redact",
                    mode=self.mode,
                    detail=f"{len(boxes)} region(s)",
                )
            )
            self._rewrite_markdown_image_links(image_path, output_path)

        return actions

    def _iter_images(self) -> list[Path]:
        candidates: list[Path] = []
        for folder in ("assets", "images", "video_data", "references"):
            base = self.skill_dir / folder
            if not base.exists():
                continue
            candidates.extend(
                path
                for path in base.rglob("*")
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
            )
        return sorted(set(candidates))

    def _detect_boxes(self, image_path: Path) -> tuple[list[tuple[int, int, int, int]], list[ImageAction]]:
        boxes: list[tuple[int, int, int, int]] = []
        actions: list[ImageAction] = []
        rel = str(image_path.relative_to(self.skill_dir))

        ocr_boxes, ocr_available = self._detect_ocr_boxes(image_path)
        boxes.extend(ocr_boxes)
        if not ocr_available:
            self.warnings.append(
                f"OCR unavailable for engine '{self.ocr_engine}'; install the required dependency."
            )
        for box in ocr_boxes:
            actions.append(ImageAction(rel, "", "ocr_text", self.mode, list(box)))

        qr_boxes, qr_available = self._detect_qr_boxes(image_path)
        boxes.extend(qr_boxes)
        if not qr_available:
            self.warnings.append("QR detection unavailable; install opencv-python-headless.")
        for box in qr_boxes:
            actions.append(ImageAction(rel, "", "qrcode", self.mode, list(box)))

        face_boxes, face_available = self._detect_face_boxes(image_path)
        boxes.extend(face_boxes)
        if not face_available:
            self.warnings.append("Face detection unavailable; install opencv-python-headless.")
        for box in face_boxes:
            actions.append(ImageAction(rel, "", "face", self.mode, list(box)))

        return self._merge_boxes(boxes), actions

    def _detect_ocr_boxes(self, image_path: Path) -> tuple[list[tuple[int, int, int, int]], bool]:
        if self.ocr_engine == "rapidocr":
            return self._detect_rapidocr_boxes(image_path)
        if self.ocr_engine == "paddleocr":
            return self._detect_paddleocr_boxes(image_path)
        return self._detect_tesseract_boxes(image_path)

    def _resolve_ocr_engine(self, requested: str) -> str:
        if requested != "auto":
            return requested
        if importlib.util.find_spec("rapidocr_onnxruntime"):
            return "rapidocr"
        if importlib.util.find_spec("paddleocr"):
            return "paddleocr"
        return "tesseract"

    def _detect_rapidocr_boxes(self, image_path: Path) -> tuple[list[tuple[int, int, int, int]], bool]:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            return [], False

        try:
            engine = RapidOCR()
            result, _ = engine(str(image_path))
        except Exception as exc:
            self.warnings.append(f"RapidOCR failed for {image_path}: {exc}")
            return [], True

        boxes: list[tuple[int, int, int, int]] = []
        for item in result or []:
            points, text = item[0], item[1]
            if not text or not self.text_sanitizer.has_sensitive(text):
                continue
            xs = [int(point[0]) for point in points]
            ys = [int(point[1]) for point in points]
            boxes.append((min(xs), min(ys), max(xs), max(ys)))
        return boxes, True

    def _detect_paddleocr_boxes(self, image_path: Path) -> tuple[list[tuple[int, int, int, int]], bool]:
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            return [], False

        try:
            engine = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False)
            result = engine.predict(str(image_path))
        except Exception as exc:
            self.warnings.append(f"PaddleOCR failed for {image_path}: {exc}")
            return [], True

        boxes: list[tuple[int, int, int, int]] = []
        for page in result or []:
            dt_polys = page.get("dt_polys", [])
            rec_texts = page.get("rec_texts", [])
            for points, text in zip(dt_polys, rec_texts):
                if not text or not self.text_sanitizer.has_sensitive(str(text)):
                    continue
                xs = [int(point[0]) for point in points]
                ys = [int(point[1]) for point in points]
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
        return boxes, True

    def _detect_tesseract_boxes(self, image_path: Path) -> tuple[list[tuple[int, int, int, int]], bool]:
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return [], False

        try:
            image = Image.open(image_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        except Exception as exc:
            self.warnings.append(f"OCR failed for {image_path}: {exc}")
            return [], True

        boxes: list[tuple[int, int, int, int]] = []
        for index, text in enumerate(data.get("text", [])):
            if not text or not self.text_sanitizer.has_sensitive(text):
                continue
            x = int(data["left"][index])
            y = int(data["top"][index])
            w = int(data["width"][index])
            h = int(data["height"][index])
            boxes.append((x, y, x + w, y + h))
        return boxes, True

    def _detect_qr_boxes(self, image_path: Path) -> tuple[list[tuple[int, int, int, int]], bool]:
        try:
            import cv2
        except ImportError:
            return [], False

        image = cv2.imread(str(image_path))
        if image is None:
            return [], True
        detector = cv2.QRCodeDetector()
        ok, points = detector.detect(image)
        if not ok or points is None:
            return [], True
        xs = [int(point[0]) for point in points[0]]
        ys = [int(point[1]) for point in points[0]]
        return [(min(xs), min(ys), max(xs), max(ys))], True

    def _detect_face_boxes(self, image_path: Path) -> tuple[list[tuple[int, int, int, int]], bool]:
        try:
            import cv2
        except ImportError:
            return [], False

        image = cv2.imread(str(image_path))
        if image is None:
            return [], True
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cascade_path = getattr(cv2.data, "haarcascades", "") + "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(cascade_path)
        if detector.empty():
            return [], False
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        return [(int(x), int(y), int(x + w), int(y + h)) for x, y, w, h in faces], True

    def _redact_image(
        self,
        input_path: Path,
        output_path: Path,
        boxes: list[tuple[int, int, int, int]],
    ) -> None:
        from PIL import Image, ImageDraw, ImageFilter

        image = Image.open(input_path).convert("RGB")
        for box in boxes:
            padded = self._pad_box(box, image.size)
            region = image.crop(padded)
            if self.mode == "blur":
                image.paste(region.filter(ImageFilter.GaussianBlur(radius=14)), padded)
            elif self.mode == "pixelate":
                small = region.resize(
                    (max(1, region.width // 12), max(1, region.height // 12)),
                    resample=Image.Resampling.BILINEAR,
                )
                image.paste(small.resize(region.size, Image.Resampling.NEAREST), padded)
            else:
                draw = ImageDraw.Draw(image)
                draw.rectangle(padded, fill="black")
        image.save(output_path)

    def _sanitized_path(self, image_path: Path) -> Path:
        rel = image_path.relative_to(self.skill_dir)
        if rel.parts and rel.parts[0] == "assets":
            return self.skill_dir / "assets_sanitized" / Path(*rel.parts[1:])
        return self.skill_dir / "assets_sanitized" / rel

    def _rewrite_markdown_image_links(self, old_path: Path, new_path: Path) -> None:
        old_rel = old_path.relative_to(self.skill_dir).as_posix()
        new_rel = new_path.relative_to(self.skill_dir).as_posix()
        for md_path in self.skill_dir.rglob("*.md"):
            content = md_path.read_text(encoding="utf-8", errors="ignore")
            updated = content.replace(old_rel, new_rel)
            updated = updated.replace(f"../{old_rel}", f"../{new_rel}")
            if updated != content:
                md_path.write_text(updated, encoding="utf-8")

    def _merge_boxes(self, boxes: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
        # Keep this conservative; overlapping boxes are fine for redaction.
        return list(dict.fromkeys(boxes))

    def _pad_box(self, box: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = box
        width, height = size
        pad = 4
        return max(0, x1 - pad), max(0, y1 - pad), min(width, x2 + pad), min(height, y2 + pad)


def load_sanitize_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required for YAML sanitize config.") from exc
        return yaml.safe_load(text) or {}
    return json.loads(text)


def sanitize_skill(args: argparse.Namespace) -> SanitizeReport:
    skill_dir = Path(args.skill_directory)
    if not skill_dir.exists():
        raise FileNotFoundError(f"Skill directory not found: {skill_dir}")

    config = load_sanitize_config(args.config)
    text_sanitizer = TextSanitizer.from_profile(args.profile, config)
    report = SanitizeReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        skill_directory=str(skill_dir),
        profile=args.profile,
        text_enabled=not args.images_only,
        image_enabled=args.images,
    )

    if not args.images_only:
        sanitize_text_files(skill_dir, text_sanitizer, report)

    if args.images:
        image_sanitizer = ImageSanitizer(
            skill_dir,
            text_sanitizer,
            args.image_mode,
            ocr_engine=args.ocr_engine,
        )
        report.image_actions.extend(image_sanitizer.sanitize_images())
        report.warnings.extend(sorted(set(image_sanitizer.warnings)))

    report_path = skill_dir / "sanitize" / "sanitize-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def sanitize_text_files(skill_dir: Path, sanitizer: TextSanitizer, report: SanitizeReport) -> None:
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".txt"}:
            continue
        if "sanitize" in path.parts:
            continue
        report.files_scanned += 1
        content = path.read_text(encoding="utf-8", errors="ignore")
        sanitized, findings = sanitizer.sanitize(content)
        if not findings:
            continue
        if sanitized != content:
            path.write_text(sanitized, encoding="utf-8")
            report.files_modified += 1
        rel = str(path.relative_to(skill_dir))
        for entity, action, count in findings:
            report.findings.append(Finding(rel, entity, action, count))


def report_to_dict(report: SanitizeReport) -> dict[str, Any]:
    data = asdict(report)
    data["summary"] = {
        "findings": sum(item.count for item in report.findings),
        "image_actions": len(report.image_actions),
        "warnings": len(report.warnings),
    }
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sanitize generated skill content")
    add_arguments(parser)
    return parser


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("skill_directory", help="Generated skill directory")
    parser.add_argument(
        "--profile",
        choices=["internal", "delivery", "public"],
        default="delivery",
        help="Sanitization profile",
    )
    parser.add_argument("--config", help="JSON/YAML sanitize config file")
    parser.add_argument("--images", action="store_true", help="Also scan/redact local images")
    parser.add_argument(
        "--images-only",
        action="store_true",
        help="Only process images; skip Markdown/JSON text sanitization",
    )
    parser.add_argument(
        "--image-mode",
        choices=["scan", "blur", "pixelate", "redact"],
        default="redact",
        help="Image action for detected regions",
    )
    parser.add_argument(
        "--ocr-engine",
        choices=["auto", "rapidocr", "paddleocr", "tesseract"],
        default="auto",
        help="OCR backend for screenshot/image text detection",
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = sanitize_skill(args)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Sanitize complete: {report.skill_directory}")
    print(f"Files scanned: {report.files_scanned}")
    print(f"Files modified: {report.files_modified}")
    print(f"Findings: {sum(item.count for item in report.findings)}")
    print(f"Image actions: {len(report.image_actions)}")
    if report.warnings:
        print(f"Warnings: {len(report.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
