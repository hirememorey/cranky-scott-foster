# L2M ↔ referee assignment coverage

Distinct **L2M games** (`l2m_reports.has_report = 1`) compared to **`referee_assignments`** rows needed for the crew pipeline (exactly one `crew_chief`, `official_2`, and `official_3` per game).

## By season

| season  | l2m_games | with_any_assignment | with_chief_row | full_trio | pct_full_trio | pct_with_chief |
| ------- | --------- | ------------------- | -------------- | --------- | ------------- | -------------- |
| 2018-19 | 170       | 170                 | 170            | 170       | 100.0         | 100.0          |
| 2019-20 | 385       | 385                 | 385            | 385       | 100.0         | 100.0          |
| 2020-21 | 402       | 402                 | 402            | 402       | 100.0         | 100.0          |
| 2021-22 | 435       | 435                 | 435            | 435       | 100.0         | 100.0          |
| 2022-23 | 470       | 470                 | 470            | 470       | 100.0         | 100.0          |
| 2023-24 | 411       | 411                 | 411            | 411       | 100.0         | 100.0          |
| 2024-25 | 428       | 428                 | 428            | 428       | 100.0         | 100.0          |

## Regular season vs playoffs

| season  | bracket        | l2m_games | full_trio | pct_full_trio |
| ------- | -------------- | --------- | --------- | ------------- |
| 2018-19 | playoffs       | 31        | 31        | 100.0         |
| 2018-19 | regular_season | 139       | 139       | 100.0         |
| 2019-20 | playoffs       | 24        | 24        | 100.0         |
| 2019-20 | regular_season | 361       | 361       | 100.0         |
| 2020-21 | playoffs       | 23        | 23        | 100.0         |
| 2020-21 | regular_season | 379       | 379       | 100.0         |
| 2021-22 | playoffs       | 26        | 26        | 100.0         |
| 2021-22 | regular_season | 409       | 409       | 100.0         |
| 2022-23 | playoffs       | 29        | 29        | 100.0         |
| 2022-23 | regular_season | 441       | 441       | 100.0         |
| 2023-24 | playoffs       | 25        | 25        | 100.0         |
| 2023-24 | regular_season | 386       | 386       | 100.0         |
| 2024-25 | playoffs       | 29        | 29        | 100.0         |
| 2024-25 | regular_season | 399       | 399       | 100.0         |

## Gaps

- L2M games **without** a full trio: **0**

_No gaps — every L2M game has a complete trio._
