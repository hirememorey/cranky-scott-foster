from referee_fatigue.taxonomy import (
    CONTINUOUS_OFF_BALL_MONITORING,
    ORDINARY_CONTACT_FOUL,
    POSSESSION_BOUNDARY_ADJUDICATION,
    STOPPAGE_REPLAY_ADMINISTRATION,
    TIMING_COUNT_JUDGMENT,
    call_detail,
    call_family,
    classify,
)


def test_classify_representative_call_types() -> None:
    cases = {
        "Foul: Shooting": ORDINARY_CONTACT_FOUL,
        "Foul: Personal": ORDINARY_CONTACT_FOUL,
        "Foul: Defense 3 Second": CONTINUOUS_OFF_BALL_MONITORING,
        "Foul: Away from Play": CONTINUOUS_OFF_BALL_MONITORING,
        "Turnover: 5 Second Violation": TIMING_COUNT_JUDGMENT,
        "Turnover: 24 Second Violation": TIMING_COUNT_JUDGMENT,
        "Violation: Lane": TIMING_COUNT_JUDGMENT,
        "Stoppage: Out-of-Bounds": POSSESSION_BOUNDARY_ADJUDICATION,
        "Turnover: Out of Bounds - Bad Pass Turn": POSSESSION_BOUNDARY_ADJUDICATION,
        "Turnover: Traveling": POSSESSION_BOUNDARY_ADJUDICATION,
        "Instant Replay: Support Ruling": STOPPAGE_REPLAY_ADMINISTRATION,
        "Stoppage: Inadvertent Whistle": STOPPAGE_REPLAY_ADMINISTRATION,
    }
    for call_type, expected in cases.items():
        assert classify(call_type) == expected


def test_classify_handles_archive_text_variants() -> None:
    assert classify("Turnover: Out of Bounds \u2013 Bad Pass Turn") == POSSESSION_BOUNDARY_ADJUDICATION
    assert classify("Turnover: Out of Bounds ? Bad Pass Turn") == POSSESSION_BOUNDARY_ADJUDICATION
    assert classify(None) == STOPPAGE_REPLAY_ADMINISTRATION


def test_call_family_and_detail_helpers() -> None:
    assert call_family("Turnover: Traveling") == "Turnover"
    assert call_detail("Turnover: Traveling") == "Traveling"
    assert call_detail("N/A") == "Unknown"
