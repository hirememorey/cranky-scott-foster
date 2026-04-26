# L2M Call Context Analysis

## Headline

- L2M events analyzed: **6,708**
- Incorrect decisions: **305**
- Baseline event error rate: **4.5%**
- Highest-risk major family: **Turnover (13.9%, n=538)**
- Highest-risk detailed call type: **Foul: Defense 3 Second (60.4%, n=53)**
- Fatigue/load context signals found: **9** with p < 0.10

## Major Call Families

| call_family | events | incorrect | error_rate |
| ----------- | ------ | --------- | ---------- |
| Turnover    | 538    | 75        | 13.9%      |
| Violation   | 107    | 12        | 11.2%      |
| Stoppage    | 298    | 17        | 5.7%       |
| Foul        | 5745   | 201       | 3.5%       |

## Highest-Risk Detailed Call Types

| call_type                               | events | incorrect | error_rate |
| --------------------------------------- | ------ | --------- | ---------- |
| Foul: Defense 3 Second                  | 53     | 32        | 60.4%      |
| Turnover: 3 Second Violation            | 22     | 9         | 40.9%      |
| Turnover: Traveling                     | 129    | 34        | 26.4%      |
| Turnover: 5 Second Violation            | 56     | 7         | 12.5%      |
| Turnover: Stepped out of Bounds         | 61     | 7         | 11.5%      |
| Turnover: Backcourt Turnover            | 20     | 2         | 10.0%      |
| Violation: Kicked Ball                  | 35     | 3         | 8.6%       |
| Stoppage: Out-of-Bounds                 | 245    | 17        | 6.9%       |
| Violation: Defensive Goaltending        | 36     | 2         | 5.6%       |
| Foul: Loose Ball                        | 530    | 22        | 4.2%       |
| Foul: Away from Play                    | 25     | 1         | 4.0%       |
| Foul: Shooting                          | 2226   | 75        | 3.4%       |
| Foul: Offensive                         | 889    | 27        | 3.0%       |
| Foul: Personal                          | 1975   | 43        | 2.2%       |
| Turnover: 24 Second Violation           | 47     | 1         | 2.1%       |
| Turnover: Out of Bounds – Bad Pass Turn | 47     | 1         | 2.1%       |
| Turnover: Lost Ball Out of Bounds       | 64     | 1         | 1.6%       |
| Stoppage: Inadvertent Whistle           | 33     | 0         | 0.0%       |

## Call vs Non-Call

| decision_kind | events | incorrect | error_rate |
| ------------- | ------ | --------- | ---------- |
| non_call      | 4718   | 244       | 5.2%       |
| call          | 1990   | 61        | 3.1%       |

## Period / Clock Context

| period_bucket | events | incorrect | error_rate |
| ------------- | ------ | --------- | ---------- |
| OT            | 710    | 38        | 5.4%       |
| Q4            | 5998   | 267       | 4.5%       |

| clock_bucket | events | incorrect | error_rate |
| ------------ | ------ | --------- | ---------- |
| 61-90s       | 1262   | 79        | 6.3%       |
| 00-30s       | 2722   | 119       | 4.4%       |
| 31-60s       | 1460   | 60        | 4.1%       |
| 91-120s      | 1264   | 47        | 3.7%       |

## Who Was Harmed On Incorrect Calls

| harmed_side | events | incorrect | error_rate |
| ----------- | ------ | --------- | ---------- |
| away        | 115    | 115       | 100.0%     |
| unknown     | 106    | 106       | 100.0%     |
| home        | 84     | 84        | 100.0%     |

## Workload Signals Within Contexts

| context              | factor                       | events | incorrect | odds_ratio | p_value |
| -------------------- | ---------------------------- | ------ | --------- | ---------- | ------- |
| clock_bucket=91-120s | days rest                    | 1256   | 47        | 0.6909     | 0.0184  |
| decision_kind=call   | days rest                    | 1977   | 60        | 0.7522     | 0.0309  |
| clock_bucket=31-60s  | games last 7d                | 1449   | 60        | 0.6776     | 0.0392  |
| clock_bucket=91-120s | back-to-back                 | 1256   | 47        | 0.1406     | 0.0606  |
| decision_kind=call   | back-to-back                 | 1977   | 60        | 0.3116     | 0.0656  |
| call_family=Stoppage | travel miles last 7d, per 1k | 298    | 17        | 1.7095     | 0.0676  |
| call_family=Turnover | travel miles last 7d, per 1k | 530    | 75        | 0.7811     | 0.0772  |
| call_family=Foul     | games last 7d                | 5703   | 199       | 0.8282     | 0.0973  |
| clock_bucket=00-30s  | travel miles last 7d, per 1k | 2702   | 119       | 0.8383     | 0.0987  |

## Interpretation

The clearest finding is contextual: error risk varies far more by call type than by broad fatigue/load variables. Treat any p < 0.10 workload signals as exploratory because they are sliced across many contexts.
