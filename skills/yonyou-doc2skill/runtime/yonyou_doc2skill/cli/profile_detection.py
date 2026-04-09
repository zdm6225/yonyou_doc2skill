"""Profile detection primitives for skill generation.

The first version stays intentionally small and rule-based. It combines
source type hints with page-level signals to produce a best-effort skill
profile and a confidence score that downstream callers can use to decide
whether to prompt for confirmation.
"""

from dataclasses import dataclass
from typing import Iterable

from yonyou_doc2skill.cli.arguments.create import SKILL_PROFILE_CHOICES

PROFILE_CHOICES = SKILL_PROFILE_CHOICES


@dataclass(frozen=True)
class ProfileDecision:
    profile: str
    confidence: float
    reasons: list[str]


PROFILE_KEYWORDS = {
    "tutorial": (
        "getting started",
        "quick start",
        "tutorial",
        "guide",
        "learn",
        "introduction",
    ),
    "reference": (
        "reference",
        "api",
        "props",
        "parameters",
        "component",
        "command",
        "options",
        "hooks",
    ),
    "builder": (
        "build",
        "generate",
        "scaffold",
        "workflow",
        "implementation",
        "integration",
    ),
    "troubleshooting": (
        "error",
        "debug",
        "troubleshooting",
        "warning",
        "issue",
        "failed",
        "fix",
    ),
    "internal-wiki": (
        "policy",
        "process",
        "approval",
        "role",
        "department",
        "internal",
        "faq",
        "standard",
    ),
}

SOURCE_PRIORS = {
    "github": {"builder": 2.5, "reference": 0.5},
    "confluence": {"internal-wiki": 3.0},
    "web": {"reference": 1.0},
    "local": {"builder": 1.5},
    "pdf": {"reference": 0.5},
}


def _normalize_signals(source_value: str, page_signals: Iterable[str] | None) -> str:
    pieces = [source_value]
    if page_signals:
        pieces.extend(page_signals)
    return " ".join(pieces).lower()


def detect_skill_profile(
    source_type: str,
    source_value: str,
    page_signals: list[str] | None = None,
) -> ProfileDecision:
    """Detect the most likely skill profile for a source.

    Args:
        source_type: Normalized source type such as web, github, or confluence.
        source_value: Raw source value or URL used for detection context.
        page_signals: Optional list of textual signals extracted from the source.

    Returns:
        ProfileDecision with the winning profile, confidence, and matched reasons.
    """
    signals = _normalize_signals(source_value, page_signals)
    scores = {profile: 0.0 for profile in PROFILE_CHOICES}

    if source_type in SOURCE_PRIORS:
        for target_profile, weight in SOURCE_PRIORS[source_type].items():
            scores[target_profile] += weight

    for profile, keywords in PROFILE_KEYWORDS.items():
        scores[profile] += sum(1 for keyword in keywords if keyword in signals)

    best_profile, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score <= 0:
        return ProfileDecision(profile="general", confidence=0.0, reasons=[])

    total_score = sum(scores.values())
    confidence = round(best_score / total_score, 2) if total_score else 0.0
    reasons = [keyword for keyword in PROFILE_KEYWORDS.get(best_profile, ()) if keyword in signals]
    return ProfileDecision(
        profile=best_profile,
        confidence=confidence,
        reasons=reasons[:5],
    )
