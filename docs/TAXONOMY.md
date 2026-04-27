# L2M Structural Decision Taxonomy

The grouping used for Sloan-, SSAC-, and blog-facing analysis lives in `src/referee_fatigue/taxonomy.py`. Categories are defined **a priori** from a human-factors lens aligned with **Wickens-style multiple resource theory (MRT)**—separating focal versus ambient monitoring and discrete versus continuous state tracking—rather than by fitting buckets to observed error rates.

## MRT-grounded categories (current `classify()` output)

Each row is the stable code returned by `classify(call_type)` and stored as `monitoring_type` in modeling pipelines.

### `focal_discrete`

**Label:** Focal / discrete (primary action)

Point-in-time judgments at the center of visual focus: ordinary shooting, personal, and offensive fouls where the official evaluates a specific contact event in the primary action area.

Examples: `Foul: Shooting`, `Foul: Personal`, `Foul: Offensive`

### `focal_continuous`

**Label:** Focal / continuous (boundary / gather)

Judgments that require tracking a player’s spatial relationship to a boundary or the ball over a short arc of motion (e.g., pivot plus ball, last touch, out of bounds).

Examples: `Turnover: Traveling`, `Stoppage: Out-of-Bounds`, `Violation: Defensive Goaltending`

### `ambient_continuous`

**Label:** Ambient / continuous (off-ball / spatial)

Divided-attention judgments away from the primary action: sustained spatial monitoring (lane, off-ball screens, away-from-play).

Examples: `Foul: Defense 3 Second`, `Foul: Away from Play`, `Turnover: Illegal Screen`

### `temporal_discrete`

**Label:** Temporal / discrete (clock / count)

Decisions that combine elapsed time or count state with a discrete triggering event (shot clock, inbound count, lane administration).

Examples: `Turnover: 24 Second Violation`, `Turnover: 5 Second Violation`, `Violation: Lane`

### `administrative_process`

**Label:** Administrative / process

Procedural stoppages, replay administration, timeouts, clock corrections, many technicals.

Examples: `Foul: Technical`, `Instant Replay: Support Ruling`, `Stoppage: TimeOut`

## Legacy labels (older reports and narrative)

Some committed **`results/*.md`** files and coach-challenge tables still use earlier slug names. Conceptual mapping:

| Legacy slug | MRT slug (`classify`) | Plain-language bucket used in blog copy |
| ----------- | --------------------- | ---------------------------------------- |
| `ordinary_contact_foul` | `focal_discrete` | Ordinary contact fouls |
| `possession_boundary_adjudication` | `focal_continuous` | Possession / boundary / gather |
| `continuous_off_ball_monitoring` | `ambient_continuous` | Continuous off-ball monitoring |
| `timing_count_judgment` | `temporal_discrete` | Timing / count |
| `stoppage_replay_administration` | `administrative_process` | Stoppage / replay / admin |

After taxonomy changes, re-run `analysis/call_context_l2m.py`, `analysis/post_event_risk_model.py`, `analysis/sori_export.py`, and `analysis/challenge_alignment.py` so all generated markdown and CSVs use the same slugs as `classify()`.

## Claims boundary

The taxonomy describes **structural context among L2M-reviewed decisions** only. It does not estimate the error rate for all NBA officiating decisions, and it must not be read as proof of measured cognitive load—only as an **operational hypothesis** linking rule types to demand profiles that can be tested further (e.g., robustness to alternate groupings, manual attention labels).
