"""Profile-specific SKILL.md sections for Doc2Skill output."""

from __future__ import annotations


def build_profile_sections(profile: str, skill_name: str) -> str:
    """Return profile-aware guidance sections for generated SKILL.md files."""
    normalized_profile = (profile or "general").strip().lower()

    sections = {
        "general": (
            "## Working with This Skill\n\n"
            f"Use this skill for general questions about {skill_name} and for practical implementation support.\n"
        ),
        "tutorial": (
            "## Learning Path\n\n"
            f"Start with the basics of {skill_name}, then move through guided examples and repeatable workflows.\n"
        ),
        "reference": (
            "## Quick lookup\n\n"
            f"Use this skill for API, command, component, and parameter lookup in {skill_name}.\n"
        ),
        "builder": (
            "## Implementation Workflow\n\n"
            f"Use this skill when turning {skill_name} source material into code, config, or build steps.\n"
        ),
        "troubleshooting": (
            "## Troubleshooting Workflow\n\n"
            f"Use this skill to diagnose {skill_name} failures, interpret errors, and narrow likely root causes.\n"
        ),
        "internal-wiki": (
            "## Organization Context\n\n"
            f"Use this skill to navigate internal {skill_name} terms, responsibilities, processes, and policy guidance.\n"
        ),
    }

    return sections.get(normalized_profile, sections["general"])
