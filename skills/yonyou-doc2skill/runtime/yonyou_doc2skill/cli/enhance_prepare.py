#!/usr/bin/env python3
"""Prepare enhancement context bundles for agent-assisted SKILL.md rewriting."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from yonyou_doc2skill.cli.constants import LOCAL_CONTENT_LIMIT, LOCAL_PREVIEW_LIMIT
from yonyou_doc2skill.cli.utils import read_reference_files


FENCED_CODE_BLOCK_RE = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)


def _read_current_skill_md(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ""
    return skill_md.read_text(encoding="utf-8")


def _collect_reference_summary(references: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    by_file: list[dict] = []
    source_counts: dict[tuple[str, str], int] = {}

    for filename, metadata in sorted(references.items()):
        item = {
            "filename": filename,
            "path": metadata.get("path", filename),
            "source": metadata.get("source", "unknown"),
            "confidence": metadata.get("confidence", "medium"),
            "size": len(metadata.get("content", "")),
        }
        by_file.append(item)
        key = (item["source"], item["confidence"])
        source_counts[key] = source_counts.get(key, 0) + 1

    by_source = [
        {"source": source, "confidence": confidence, "count": count}
        for (source, confidence), count in sorted(source_counts.items())
    ]
    return by_file, by_source


def _extract_examples(references: dict[str, dict], limit: int = 8) -> list[dict]:
    examples: list[dict] = []

    for filename, metadata in references.items():
        content = metadata.get("content", "")
        for match in FENCED_CODE_BLOCK_RE.finditer(content):
            language = (match.group(1) or "text").strip() or "text"
            snippet = match.group(2).strip()
            if not snippet:
                continue
            lines = snippet.splitlines()
            if len(lines) > 20:
                snippet = "\n".join(lines[:20]) + "\n..."
            examples.append(
                {
                    "filename": filename,
                    "path": metadata.get("path", filename),
                    "source": metadata.get("source", "unknown"),
                    "confidence": metadata.get("confidence", "medium"),
                    "language": language,
                    "snippet": snippet,
                }
            )
            if len(examples) >= limit:
                return examples

    return examples


def _build_reference_map(reference_files: list[dict]) -> str:
    lines = ["# Reference Map", "", "下面这些 references 是增强时优先查阅的语料地图。", ""]
    if not reference_files:
        lines.extend(["- 当前没有 references 文件。", ""])
        return "\n".join(lines)

    for item in reference_files:
        lines.append(
            f"- `{item['filename']}`: 来源={item['source']}，置信度={item['confidence']}，"
            f"大小约 {item['size']} 字符，路径=`{item['path']}`"
        )
    lines.append("")
    return "\n".join(lines)


def _build_examples_doc(examples: list[dict]) -> str:
    lines = [
        "# High Value Examples",
        "",
        "下面是从 references 里抽出的高价值代码或配置片段，优先可用于增强后的 Quick Reference。",
        "",
    ]
    if not examples:
        lines.extend(["- 当前未抽取到 fenced code block，可改为从正文结构中提炼示例。", ""])
        return "\n".join(lines)

    for idx, example in enumerate(examples, 1):
        lines.extend(
            [
                f"## Example {idx}",
                "",
                f"- 文件: `{example['filename']}`",
                f"- 来源: `{example['source']}`",
                f"- 置信度: `{example['confidence']}`",
                "",
                f"```{example['language']}",
                example["snippet"],
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _build_discrepancies_doc(references: dict[str, dict]) -> str:
    conflict_files = [
        metadata.get("path", filename)
        for filename, metadata in sorted(references.items())
        if metadata.get("source") == "conflicts" or "conflicts" in metadata.get("path", "")
    ]
    lines = [
        "# Discrepancies",
        "",
        "这里记录增强时需要重点关注的冲突或边界。没有显式冲突文件时，也要注意不同来源之间的语气和抽象层级差异。",
        "",
    ]
    if not conflict_files:
        lines.extend(["- 当前没有发现显式 `conflicts` 参考文件。", ""])
        return "\n".join(lines)

    for path in conflict_files:
        lines.append(f"- 发现冲突文件: `{path}`")
    lines.append("")
    return "\n".join(lines)


def _build_rewrite_outline(intent: str | None) -> str:
    lines = [
        "# Rewrite Outline",
        "",
        "建议增强后的 `SKILL.md` 按下面骨架重写。",
        "",
        "1. 适用范围",
        "2. 不处理事项",
        "3. 关键规则",
        "4. 快速路由",
        "5. 主要工作流程",
        "6. 回答规则 / 边界说明",
        "7. 高价值问法与参考文件地图",
        "",
    ]
    if intent:
        lines.extend([f"- 本次增强目标: {intent}", ""])
    return "\n".join(lines)


def _build_enhance_brief(
    skill_dir: Path,
    current_skill_md: str,
    by_source: list[dict],
    reference_files: list[dict],
    intent: str | None,
) -> str:
    source_summary = ", ".join(
        f"{item['source']}({item['confidence']}:{item['count']})" for item in by_source
    ) or "无 references"
    lines = [
        "# Enhance Brief",
        "",
        f"- Skill 目录: `{skill_dir}`",
        f"- 当前 references 文件数: {len(reference_files)}",
        f"- 来源概览: {source_summary}",
        f"- 当前是否已有 SKILL.md: {'是' if current_skill_md else '否'}",
        f"- 本次模式: agent-assisted prepare",
        "",
        "本次 `prepare` 不会直接改写 `SKILL.md`。后续应由当前对话 agent 读取本目录下的 bundle，",
        "结合用户当前目标，重写出更可路由、更像专家助手的 `SKILL.md`。",
        "",
    ]
    if intent:
        lines.extend([f"- 用户增强目标: {intent}", ""])
    lines.extend(
        [
            "优先增强点：",
            "",
            "- 补清晰的触发条件和快速路由",
            "- 把 references 变成明确的文件地图",
            "- 提炼高价值样例和典型问法",
            "- 说明边界、冲突来源和回答规则",
            "",
        ]
    )
    return "\n".join(lines)


def _build_prompt(intent: str | None) -> str:
    lines = [
        "# Prompt",
        "",
        "请基于当前 skill 目录中的 `SKILL.md`、`references/` 和本 `.enhance/` 目录的材料，",
        "重写一个更适合当前 agent 路由和使用的 `SKILL.md`。",
        "",
        "要求：",
        "",
        "- 不要重新抓取来源",
        "- 不要虚构 references 里不存在的能力",
        "- 优先输出可执行流程，而不是泛泛介绍",
        "- 补充典型问法、边界说明、参考文件地图、工作流路由",
        "",
    ]
    if intent:
        lines.extend([f"- 用户目标: {intent}", ""])
    return "\n".join(lines)


def generate_enhancement_bundle(
    skill_dir: str | Path,
    *,
    intent: str | None = None,
    output_dir: str | Path | None = None,
) -> Path:
    """Generate an enhancement context bundle without modifying SKILL.md."""
    skill_path = Path(skill_dir)
    bundle_dir = Path(output_dir) if output_dir else skill_path / ".enhance"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    current_skill_md = _read_current_skill_md(skill_path)
    references = read_reference_files(
        skill_path,
        max_chars=LOCAL_CONTENT_LIMIT,
        preview_limit=LOCAL_PREVIEW_LIMIT,
    )
    reference_files, by_source = _collect_reference_summary(references)
    examples = _extract_examples(references)

    manifest = {
        "skill_dir": str(skill_path.resolve()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "prepare",
        "intent": intent,
        "reference_count": len(reference_files),
        "sources": by_source,
        "files": [item["path"] for item in reference_files],
    }
    status = {
        "status": "prepared",
        "intent": intent,
        "bundle_dir": str(bundle_dir.resolve()),
    }

    (bundle_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (bundle_dir / "status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (bundle_dir / "enhance-brief.md").write_text(
        _build_enhance_brief(skill_path, current_skill_md, by_source, reference_files, intent),
        encoding="utf-8",
    )
    (bundle_dir / "reference-map.md").write_text(
        _build_reference_map(reference_files),
        encoding="utf-8",
    )
    (bundle_dir / "high-value-examples.md").write_text(
        _build_examples_doc(examples),
        encoding="utf-8",
    )
    (bundle_dir / "discrepancies.md").write_text(
        _build_discrepancies_doc(references),
        encoding="utf-8",
    )
    (bundle_dir / "rewrite-outline.md").write_text(
        _build_rewrite_outline(intent),
        encoding="utf-8",
    )
    (bundle_dir / "prompt.md").write_text(_build_prompt(intent), encoding="utf-8")

    return bundle_dir
