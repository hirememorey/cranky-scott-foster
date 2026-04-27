"""Pre-specified L2M decision-context taxonomy.

The categories in this module are intentionally rule-based. They should be
changed rarely and with documentation updates because downstream reports treat
them as the paper's fixed structural taxonomy, not as model-tuned features.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


ORDINARY_CONTACT_FOUL = "ordinary_contact_foul"
CONTINUOUS_OFF_BALL_MONITORING = "continuous_off_ball_monitoring"
TIMING_COUNT_JUDGMENT = "timing_count_judgment"
POSSESSION_BOUNDARY_ADJUDICATION = "possession_boundary_adjudication"
STOPPAGE_REPLAY_ADMINISTRATION = "stoppage_replay_administration"


@dataclass(frozen=True)
class CategoryDefinition:
    """Human-readable category metadata for reports and methods docs."""

    category: str
    label: str
    rationale: str
    examples: tuple[str, ...]


CATEGORY_DEFINITIONS: dict[str, CategoryDefinition] = {
    ORDINARY_CONTACT_FOUL: CategoryDefinition(
        category=ORDINARY_CONTACT_FOUL,
        label="Ordinary contact foul",
        rationale=(
            "Primary-action contact judgments such as shooting, personal, "
            "offensive, and technical fouls. These require contact evaluation "
            "but generally not continuous state tracking away from the ball."
        ),
        examples=("Foul: Shooting", "Foul: Personal", "Foul: Offensive"),
    ),
    CONTINUOUS_OFF_BALL_MONITORING: CategoryDefinition(
        category=CONTINUOUS_OFF_BALL_MONITORING,
        label="Continuous off-ball monitoring",
        rationale=(
            "Judgments that require officials to monitor players or spatial "
            "relationships away from the immediate ball action over time."
        ),
        examples=("Foul: Defense 3 Second", "Foul: Away from Play", "Foul: Loose Ball"),
    ),
    TIMING_COUNT_JUDGMENT: CategoryDefinition(
        category=TIMING_COUNT_JUDGMENT,
        label="Timing/count judgment",
        rationale=(
            "Rule decisions driven by elapsed time, count state, or clock/lane "
            "administration rather than ordinary contact."
        ),
        examples=("Turnover: 5 Second Violation", "Turnover: 24 Second Violation", "Violation: Lane"),
    ),
    POSSESSION_BOUNDARY_ADJUDICATION: CategoryDefinition(
        category=POSSESSION_BOUNDARY_ADJUDICATION,
        label="Possession/boundary adjudication",
        rationale=(
            "Boundary, last-touch, possession-control, and movement-rule "
            "decisions where the key question is who controlled the ball or "
            "whether a player/ball crossed a legal boundary."
        ),
        examples=("Stoppage: Out-of-Bounds", "Turnover: Traveling", "Turnover: Backcourt Turnover"),
    ),
    STOPPAGE_REPLAY_ADMINISTRATION: CategoryDefinition(
        category=STOPPAGE_REPLAY_ADMINISTRATION,
        label="Stoppage/replay administration",
        rationale=(
            "Administrative stoppages, replay support/overturn rulings, clock "
            "corrections, timeout administration, and other process decisions."
        ),
        examples=("Stoppage: Inadvertent Whistle", "Instant Replay: Support Ruling", "Stoppage: Clock"),
    ),
}


def classify(call_type: str | None, review_decision: str | None = None) -> str:
    """Classify an L2M call type into the fixed structural taxonomy."""
    del review_decision  # Reserved for future pre-specified non-call handling.
    text = _normalize(call_type)
    if not text or text == "n/a":
        return STOPPAGE_REPLAY_ADMINISTRATION

    if "defense 3 second" in text or "defensive 3 second" in text:
        return CONTINUOUS_OFF_BALL_MONITORING
    if any(token in text for token in _TIMING_TOKENS):
        return TIMING_COUNT_JUDGMENT
    if any(token in text for token in _POSSESSION_BOUNDARY_TOKENS):
        return POSSESSION_BOUNDARY_ADJUDICATION
    if any(token in text for token in _STOPPAGE_TOKENS):
        return STOPPAGE_REPLAY_ADMINISTRATION
    if any(token in text for token in _OFF_BALL_TOKENS):
        return CONTINUOUS_OFF_BALL_MONITORING
    return ORDINARY_CONTACT_FOUL


def call_family(value: str | None) -> str:
    """Return the prefix before ':' for a raw L2M call type."""
    if not value:
        return "Unknown"
    return str(value).split(":", 1)[0].strip()


def call_detail(value: str | None) -> str:
    """Return the detail after ':' for a raw L2M call type."""
    if not value or ":" not in str(value):
        return "Unknown"
    return str(value).split(":", 1)[1].strip()


def category_labels() -> dict[str, str]:
    """Map category identifiers to presentation labels."""
    return {
        key: definition.label
        for key, definition in CATEGORY_DEFINITIONS.items()
    }


_STOPPAGE_TOKENS = (
    "stoppage",
    "instant replay",
    "timeout",
    "time out",
    "clock",
    "inadvertent whistle",
    "delay of game",
    "jump ball",
    "free throw technical",
)

_TIMING_TOKENS = (
    "3 second violation",
    "5 second",
    "8 second",
    "10 second",
    "24 second",
    "lane",
)

_POSSESSION_BOUNDARY_TOKENS = (
    "out of bounds",
    "out-of-bounds",
    "stepped out",
    "traveling",
    "backcourt",
    "bad pass",
    "lost ball",
    "inbound turnover",
    "palming",
    "double dribble",
    "discontinue dribble",
    "kicked ball",
    "goaltending",
)

_OFF_BALL_TOKENS = (
    "away from play",
    "loose ball",
    "screen",
)


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("?", "-")
    text = re.sub(r"[-_/]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
