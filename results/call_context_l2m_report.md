# L2M Call Context Analysis

## Headline

- L2M events analyzed: **51,130**
- Incorrect decisions: **3,214**
- Baseline event error rate: **6.3%**
- Highest-risk major family: **Turnover (19.5%, n=3662)**
- Highest-risk detailed call type: **Violation: Lane (45.3%, n=95)**
- Fatigue/load context signals found: **15** with p < 0.10

## Major Call Families

| call_family    | events | incorrect | error_rate |
| -------------- | ------ | --------- | ---------- |
| Turnover       | 3662   | 715       | 19.5%      |
| Violation      | 607    | 92        | 15.2%      |
| Stoppage       | 1071   | 77        | 7.2%       |
| Foul           | 45699  | 2322      | 5.1%       |
| Instant Replay | 65     | 0         | 0.0%       |

## Structural Taxonomy

| taxonomy_category      | events | incorrect | error_rate |
| ---------------------- | ------ | --------- | ---------- |
| temporal_discrete      | 1080   | 214       | 19.8%      |
| focal_continuous       | 3993   | 644       | 16.1%      |
| ambient_continuous     | 5907   | 568       | 9.6%       |
| administrative_process | 505    | 31        | 6.1%       |
| focal_discrete         | 39645  | 1757      | 4.4%       |

## Highest-Risk Detailed Call Types

| call_type                       | events | incorrect | error_rate |
| ------------------------------- | ------ | --------- | ---------- |
| Violation: Lane                 | 95     | 43        | 45.3%      |
| Turnover: 5 Second Inbound      | 41     | 16        | 39.0%      |
| Foul: Defense 3 Second          | 681    | 244       | 35.8%      |
| Turnover: Traveling             | 1132   | 390       | 34.5%      |
| Turnover: Discontinue Dribble   | 37     | 11        | 29.7%      |
| Turnover: 3 Second Violation    | 289    | 83        | 28.7%      |
| N/A                             | 22     | 6         | 27.3%      |
| Turnover: Double Dribble        | 98     | 19        | 19.4%      |
| Turnover: Inbound Turnover      | 22     | 4         | 18.2%      |
| Turnover: 5 Second Violation    | 280    | 48        | 17.1%      |
| Turnover: Out of Bounds         | 131    | 21        | 16.0%      |
| Turnover: Stepped out of Bounds | 299    | 45        | 15.1%      |
| Turnover: Palming               | 83     | 12        | 14.5%      |
| Violation: Delay of Game        | 63     | 9         | 14.3%      |
| Turnover: Offensive Goaltending | 73     | 10        | 13.7%      |
| Turnover: 8 Second Violation    | 79     | 8         | 10.1%      |
| Violation: Jump Ball            | 31     | 3         | 9.7%       |
| Violation: Kicked Ball          | 181    | 17        | 9.4%       |
| Turnover: Backcourt Turnover    | 99     | 8         | 8.1%       |
| Stoppage: Out-of-Bounds         | 912    | 70        | 7.7%       |

## Call vs Non-Call

| decision_kind | events | incorrect | error_rate |
| ------------- | ------ | --------- | ---------- |
| non_call      | 39153  | 2743      | 7.0%       |
| call          | 11977  | 471       | 3.9%       |

## Period / Clock Context

| period_bucket | events | incorrect | error_rate |
| ------------- | ------ | --------- | ---------- |
| OT            | 5994   | 422       | 7.0%       |
| Q4            | 45136  | 2792      | 6.2%       |

| clock_bucket | events | incorrect | error_rate |
| ------------ | ------ | --------- | ---------- |
| 31-60s       | 11672  | 794       | 6.8%       |
| 61-90s       | 10303  | 678       | 6.6%       |
| 91-120s      | 10325  | 649       | 6.3%       |
| 00-30s       | 18830  | 1093      | 5.8%       |

## Who Was Harmed On Incorrect Calls

| harmed_side | events | incorrect | error_rate |
| ----------- | ------ | --------- | ---------- |
| away        | 1152   | 1152      | 100.0%     |
| home        | 1109   | 1109      | 100.0%     |
| unknown     | 953    | 953       | 100.0%     |

## Workload Signals Within Contexts

| context                | factor                       | events | incorrect | odds_ratio | p_value |
| ---------------------- | ---------------------------- | ------ | --------- | ---------- | ------- |
| clock_bucket=31-60s    | games last 7d                | 9187   | 639       | 0.8466     | 0.0046  |
| call_family=Violation  | back-to-back                 | 499    | 75        | 3.1186     | 0.0077  |
| call_family=Stoppage   | games last 7d                | 1036   | 74        | 0.6420     | 0.0108  |
| decision_kind=call     | games last 7d                | 9720   | 368       | 0.8421     | 0.0197  |
| call_family=Turnover   | games last 7d                | 3034   | 584       | 0.8557     | 0.0248  |
| decision_kind=non_call | games last 7d                | 30992  | 2184      | 0.9300     | 0.0278  |
| decision_kind=call     | days rest                    | 9720   | 368       | 0.9079     | 0.0354  |
| call_family=Foul       | games last 7d                | 36069  | 1813      | 0.9354     | 0.0600  |
| clock_bucket=00-30s    | travel miles last 7d, per 1k | 15118  | 853       | 0.9281     | 0.0646  |
| call_family=Violation  | days rest                    | 499    | 75        | 1.2071     | 0.0829  |
| clock_bucket=00-30s    | games last 7d                | 15118  | 853       | 0.9162     | 0.0845  |
| call_family=Stoppage   | back-to-back                 | 1036   | 74        | 0.3411     | 0.0888  |
| clock_bucket=00-30s    | full-game pace, per 5 poss   | 15118  | 853       | 0.9389     | 0.0924  |
| call_family=Turnover   | travel miles last 7d, per 1k | 3034   | 584       | 0.9122     | 0.0934  |
| clock_bucket=31-60s    | Q4 pre-L2M actions/min       | 9187   | 639       | 0.9392     | 0.0952  |

## Interpretation

The clearest finding is contextual: error risk varies far more by call type than by broad fatigue/load variables. Treat any p < 0.10 workload signals as exploratory because they are sliced across many contexts.
