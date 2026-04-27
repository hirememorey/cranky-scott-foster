"""Pre-specified L2M decision-context taxonomy based on Multiple Resource Theory (MRT).

The categories in this module are defined by their cognitive demand profiles
(focal vs. ambient monitoring, discrete vs. continuous state tracking) rather 
than observed error rates. This ensures the taxonomy remains a priori and 
defensible for academic research.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


# MRT-Grounded Categories
FOCAL_DISCRETE = "focal_discrete"
FOCAL_CONTINUOUS = "focal_continuous"
AMBIENT_CONTINUOUS = "ambient_continuous"
TEMPORAL_DISCRETE = "temporal_discrete"
ADMINISTRATIVE_PROCESS = "administrative_process"


@dataclass(frozen=True)
class CategoryDefinition:
    """Human-readable category metadata for reports and methods docs."""

    category: str
    label: str
    rationale: str
    examples: tuple[str, ...]


CATEGORY_DEFINITIONS: dict[str, CategoryDefinition] = {
    FOCAL_DISCRETE: CategoryDefinition(
        category=FOCAL_DISCRETE,
        label="Focal/Discrete (Primary Action)",
        rationale=(
            "Point-in-time judgments occurring at the center of visual focus. "
            "Includes shooting and personal fouls where the official evaluates "
            "a specific contact event in the primary action area."
        ),
        examples=("Foul: Shooting", "Foul: Personal", "Foul: Offensive"),
    ),
    FOCAL_CONTINUOUS: CategoryDefinition(
        category=FOCAL_CONTINUOUS,
        label="Focal/Continuous (Boundary/Gather)",
        rationale=(
            "Judgments requiring continuous monitoring of a player's spatial "
            "relationship to a boundary or the ball. Includes traveling, "
            "out-of-bounds, and goaltending, which require tracking multiple "
            "moving points (e.g., pivot foot and ball) simultaneously."
        ),
        examples=("Turnover: Traveling", "Stoppage: Out-of-Bounds", "Violation: Defensive Goaltending"),
    ),
    AMBIENT_CONTINUOUS: CategoryDefinition(
        category=AMBIENT_CONTINUOUS,
        label="Ambient/Continuous (Off-Ball/Spatial)",
        rationale=(
            "Judgments requiring 'divided attention' away from the primary "
            "action. Includes defensive three seconds and off-ball screens, "
            "where the official must maintain a secondary monitor of player "
            "positioning within a spatial area over time."
        ),
        examples=("Foul: Defense 3 Second", "Foul: Away from Play", "Turnover: Illegal Screen"),
    ),
    TEMPORAL_DISCRETE: CategoryDefinition(
        category=TEMPORAL_DISCRETE,
        label="Temporal/Discrete (Clock/Count)",
        rationale=(
            "Judgments driven by the intersection of time and a discrete "
            "event. Includes shot clock, 5/8-second violations, and lane "
            "violations, where the official must coordinate a mental or "
            "mechanical count with player movement."
        ),
        examples=("Turnover: 24 Second Violation", "Turnover: 5 Second Violation", "Violation: Lane"),
    ),
    ADMINISTRATIVE_PROCESS: CategoryDefinition(
        category=ADMINISTRATIVE_PROCESS,
        label="Administrative/Process",
        rationale=(
            "Non-gameplay decisions including technical fouls, timeouts, "
            "replay administration, and clock management. These are "
            "procedural rather than observational in nature."
        ),
        examples=("Foul: Technical", "Instant Replay: Support Ruling", "Stoppage: TimeOut"),
    ),
}


def classify(call_type: str | None, review_decision: str | None = None) -> str:
    """Classify an L2M call type into the MRT-grounded taxonomy."""
    del review_decision
    text = _normalize(call_type)
    if not text or text == "n/a":
        return ADMINISTRATIVE_PROCESS

    # 1. Ambient/Continuous (Highest conflict - off-ball state tracking)
    if any(token in text for token in _AMBIENT_CONTINUOUS_TOKENS):
        return AMBIENT_CONTINUOUS

    # 2. Temporal/Discrete (Medium conflict - temporal/event coordination)
    if any(token in text for token in _TEMPORAL_DISCRETE_TOKENS):
        return TEMPORAL_DISCRETE

    # 3. Focal/Continuous (Medium conflict - spatial/event tracking)
    if any(token in text for token in _FOCAL_CONTINUOUS_TOKENS):
        return FOCAL_CONTINUOUS

    # 4. Administrative/Process (Procedural)
    if any(token in text for token in _ADMIN_TOKENS):
        return ADMINISTRATIVE_PROCESS

    # 5. Focal/Discrete (Baseline - primary action contact)
    return FOCAL_DISCRETE


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


_ADMIN_TOKENS = (
    "stoppage",
    "instant replay",
    "timeout",
    "time out",
    "clock",
    "inadvertent whistle",
    "delay of game",
    "jump ball",
    "technical",
    "flagrant",
    "clear path",
)

_TEMPORAL_DISCRETE_TOKENS = (
    "3 second violation",
    "5 second",
    "8 second",
    "10 second",
    "24 second",
    "lane",
)

_FOCAL_CONTINUOUS_TOKENS = (
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

_AMBIENT_CONTINUOUS_TOKENS = (
    "defense 3 second",
    "defensive 3 second",
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


# Backward-compatible names: same string values as MRT categories above (what `classify` returns).
ORDINARY_CONTACT_FOUL = FOCAL_DISCRETE
POSSESSION_BOUNDARY_ADJUDICATION = FOCAL_CONTINUOUS
CONTINUOUS_OFF_BALL_MONITORING = AMBIENT_CONTINUOUS
TIMING_COUNT_JUDGMENT = TEMPORAL_DISCRETE
STOPPAGE_REPLAY_ADMINISTRATION = ADMINISTRATIVE_PROCESS

