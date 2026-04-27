# L2M Structural Decision Taxonomy

This taxonomy is the pre-specified grouping used for Sloan-style analysis of NBA Last Two Minute report events. It is intentionally rule-based and lives in `src/referee_fatigue/taxonomy.py` so descriptive reports, models, and SORI exports use the same definitions.

## Categories

### `ordinary_contact_foul`

Primary-action contact judgments such as shooting, personal, offensive, and technical fouls. These require contact evaluation but generally not continuous state tracking away from the ball.

Examples: `Foul: Shooting`, `Foul: Personal`, `Foul: Offensive`.

### `continuous_off_ball_monitoring`

Judgments that require officials to monitor players or spatial relationships away from the immediate ball action over time.

Examples: `Foul: Defense 3 Second`, `Foul: Away from Play`, `Foul: Loose Ball`.

### `timing_count_judgment`

Rule decisions driven by elapsed time, count state, or clock/lane administration rather than ordinary contact.

Examples: `Turnover: 5 Second Violation`, `Turnover: 24 Second Violation`, `Violation: Lane`.

### `possession_boundary_adjudication`

Boundary, last-touch, possession-control, and movement-rule decisions where the key question is who controlled the ball or whether a player/ball crossed a legal boundary.

Examples: `Stoppage: Out-of-Bounds`, `Turnover: Traveling`, `Turnover: Backcourt Turnover`.

### `stoppage_replay_administration`

Administrative stoppages, replay support/overturn rulings, clock corrections, timeout administration, and other process decisions.

Examples: `Stoppage: Inadvertent Whistle`, `Instant Replay: Support Ruling`, `Stoppage: Clock`.

## Claims Boundary

The taxonomy describes structural context among L2M-reviewed decisions only. It does not estimate the error rate for all NBA officiating decisions, and it should not be used to claim individual referee skill differences from the current sample.
