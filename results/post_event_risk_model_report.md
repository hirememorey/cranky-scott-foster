# Post-Event L2M Bad-Call Risk Model

## Headline

- Events available: **6,657**
- Train events: **4,979**
- Test events: **1,678**
- Test baseline error rate: **5.0%**
- ROC AUC: **0.724**
- Average precision: **0.315**
- Brier score: **0.0411**
- Log loss: **0.1685**
- Decision: **usable post-event risk ranking**

## Risk Lift

| risk_bucket | events | incorrect | observed_error_rate | lift_vs_baseline | share_of_all_errors_captured | avg_predicted_probability |
| ----------- | ------ | --------- | ------------------- | ---------------- | ---------------------------- | ------------------------- |
| top_5pct    | 83     | 31        | 37.3%               | 7.461            | 36.9%                        | 25.2%                     |
| top_10pct   | 167    | 35        | 21.0%               | 4.187            | 41.7%                        | 16.9%                     |
| top_20pct   | 335    | 45        | 13.4%               | 2.683            | 53.6%                        | 11.3%                     |
| top_33pct   | 553    | 55        | 9.9%                | 1.987            | 65.5%                        | 8.6%                      |

## Calibration By Risk Decile

| risk_decile | events | incorrect | observed_error_rate | avg_predicted_probability |
| ----------- | ------ | --------- | ------------------- | ------------------------- |
| D10         | 168    | 35        | 20.8%               | 16.8%                     |
| D9          | 168    | 10        | 6.0%                | 5.7%                      |
| D8          | 168    | 9         | 5.4%                | 4.5%                      |
| D7          | 167    | 2         | 1.2%                | 3.8%                      |
| D6          | 168    | 2         | 1.2%                | 3.3%                      |
| D5          | 168    | 10        | 6.0%                | 2.9%                      |
| D4          | 167    | 6         | 3.6%                | 2.5%                      |
| D3          | 168    | 4         | 2.4%                | 2.2%                      |
| D2          | 168    | 2         | 1.2%                | 1.8%                      |
| D1          | 168    | 4         | 2.4%                | 1.4%                      |

## Strongest Positive Risk Features

| feature                                            | coefficient | odds_ratio |
| -------------------------------------------------- | ----------- | ---------- |
| call_type_grouped_Foul: Defense 3 Second           | 1.454       | 4.279      |
| monitoring_type_timing_count                       | 1.069       | 2.912      |
| call_type_grouped_Turnover: Traveling              | 1.009       | 2.744      |
| call_type_grouped_Stoppage: Out-of-Bounds          | 0.593       | 1.809      |
| call_family_Violation                              | 0.421       | 1.524      |
| call_type_grouped_Other                            | 0.313       | 1.367      |
| clock_bucket_61-90s                                | 0.296       | 1.344      |
| decision_kind_non_call                             | 0.196       | 1.217      |
| call_type_grouped_Foul: Shooting                   | 0.171       | 1.186      |
| call_family_Turnover                               | 0.151       | 1.163      |
| monitoring_type_possession_boundary                | 0.148       | 1.160      |
| call_type_grouped_Turnover: 3 Second Violation     | 0.146       | 1.157      |
| call_type_grouped_Violation: Kicked Ball           | 0.091       | 1.095      |
| clock_bucket_00-30s                                | 0.086       | 1.090      |
| clock_seconds                                      | 0.067       | 1.069      |
| call_type_grouped_Foul: Loose Ball                 | 0.050       | 1.052      |
| period_bucket_Q4                                   | 0.045       | 1.046      |
| back_to_back                                       | 0.019       | 1.020      |
| clock_bucket_31-60s                                | 0.019       | 1.019      |
| l2m_actions_per_minute                             | -0.039      | 0.962      |
| call_type_grouped_Violation: Defensive Goaltending | -0.045      | 0.956      |
| call_family_Foul                                   | -0.049      | 0.952      |
| estimated_pace                                     | -0.049      | 0.952      |
| travel_miles_last_7k                               | -0.068      | 0.935      |
| q4_pre_l2m_actions_per_minute                      | -0.072      | 0.930      |

## Interpretation

This model is designed to rank reviewed L2M events by structural error risk, not to predict every bad call perfectly. The key question is whether the top-risk bucket beats the held-out baseline of 5.0%. In the top 10% of scored events, the observed error rate was 21.0%, a 4.2x lift.
