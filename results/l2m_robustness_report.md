# L2M Robustness Checks

Rolling season holdout after excluding key call types or structural categories.

## Average By Scenario

| scenario                                 | scenario_events | scenario_error_rate | holdout_seasons | mean_roc_auc | mean_top_10_lift | mean_top_10_error_rate | mean_error_capture |
| ---------------------------------------- | --------------- | ------------------- | --------------- | ------------ | ---------------- | ---------------------- | ------------------ |
| full_sample                              | 51130           | 6.3%                | 6               | 0.687        | 3.538            | 21.7%                  | 35.4%              |
| exclude_defense_3_second                 | 50449           | 5.9%                | 6               | 0.666        | 3.137            | 17.9%                  | 31.4%              |
| exclude_traveling                        | 49998           | 5.6%                | 6               | 0.653        | 2.897            | 15.9%                  | 29.0%              |
| exclude_defense_3_second_and_traveling   | 49317           | 5.2%                | 6               | 0.625        | 2.388            | 12.1%                  | 23.9%              |
| exclude_rare_call_types_lt_100           | 49850           | 6.1%                | 6               | 0.679        | 3.342            | 19.7%                  | 33.4%              |
| exclude_timing_count_judgment            | 50050           | 6.0%                | 6               | 0.672        | 3.218            | 18.7%                  | 32.2%              |
| exclude_possession_boundary_adjudication | 47137           | 5.5%                | 6               | 0.645        | 2.829            | 14.8%                  | 28.3%              |

## By Scenario And Season

| scenario                                 | holdout_season | scenario_events | scenario_error_rate | test_events | baseline_error_rate | roc_auc | avg_precision | top_10_error_rate | top_10_lift | top_10_error_capture |
| ---------------------------------------- | -------------- | --------------- | ------------------- | ----------- | ------------------- | ------- | ------------- | ----------------- | ----------- | -------------------- |
| full_sample                              | 2019-20        | 51130           | 6.3%                | 7514        | 6.8%                | 0.655   | 0.159         | 18.6%             | 2.741       | 27.4%                |
| full_sample                              | 2020-21        | 51130           | 6.3%                | 7345        | 5.9%                | 0.657   | 0.196         | 18.8%             | 3.175       | 31.7%                |
| full_sample                              | 2021-22        | 51130           | 6.3%                | 8171        | 7.7%                | 0.678   | 0.218         | 26.4%             | 3.451       | 34.5%                |
| full_sample                              | 2022-23        | 51130           | 6.3%                | 10591       | 6.2%                | 0.727   | 0.224         | 24.4%             | 3.933       | 39.3%                |
| full_sample                              | 2023-24        | 51130           | 6.3%                | 7678        | 6.0%                | 0.709   | 0.227         | 23.6%             | 3.922       | 39.2%                |
| full_sample                              | 2024-25        | 51130           | 6.3%                | 6708        | 4.5%                | 0.696   | 0.205         | 18.2%             | 4.005       | 40.0%                |
| exclude_defense_3_second                 | 2019-20        | 50449           | 5.9%                | 7440        | 6.6%                | 0.649   | 0.155         | 17.7%             | 2.672       | 26.7%                |
| exclude_defense_3_second                 | 2020-21        | 50449           | 5.9%                | 7293        | 5.8%                | 0.649   | 0.189         | 17.7%             | 3.065       | 30.6%                |
| exclude_defense_3_second                 | 2021-22        | 50449           | 5.9%                | 8025        | 7.2%                | 0.658   | 0.195         | 21.3%             | 2.981       | 29.8%                |
| exclude_defense_3_second                 | 2022-23        | 50449           | 5.9%                | 10376       | 5.6%                | 0.705   | 0.197         | 19.3%             | 3.421       | 34.2%                |
| exclude_defense_3_second                 | 2023-24        | 50449           | 5.9%                | 7571        | 5.4%                | 0.675   | 0.182         | 17.4%             | 3.236       | 32.4%                |
| exclude_defense_3_second                 | 2024-25        | 50449           | 5.9%                | 6655        | 4.1%                | 0.664   | 0.159         | 14.1%             | 3.446       | 34.4%                |
| exclude_traveling                        | 2019-20        | 49998           | 5.6%                | 7355        | 6.2%                | 0.614   | 0.110         | 13.5%             | 2.173       | 21.7%                |
| exclude_traveling                        | 2020-21        | 49998           | 5.6%                | 7195        | 5.2%                | 0.606   | 0.118         | 12.1%             | 2.340       | 23.4%                |
| exclude_traveling                        | 2021-22        | 49998           | 5.6%                | 7972        | 6.9%                | 0.647   | 0.166         | 19.6%             | 2.832       | 28.3%                |
| exclude_traveling                        | 2022-23        | 49998           | 5.6%                | 10334       | 5.5%                | 0.697   | 0.176         | 17.8%             | 3.252       | 32.5%                |
| exclude_traveling                        | 2023-24        | 49998           | 5.6%                | 7500        | 5.4%                | 0.683   | 0.211         | 18.1%             | 3.350       | 33.5%                |
| exclude_traveling                        | 2024-25        | 49998           | 5.6%                | 6579        | 4.1%                | 0.673   | 0.211         | 14.2%             | 3.436       | 34.3%                |
| exclude_defense_3_second_and_traveling   | 2019-20        | 49317           | 5.2%                | 7281        | 6.0%                | 0.607   | 0.106         | 12.4%             | 2.050       | 20.5%                |
| exclude_defense_3_second_and_traveling   | 2020-21        | 49317           | 5.2%                | 7143        | 5.0%                | 0.594   | 0.111         | 10.9%             | 2.180       | 21.8%                |
| exclude_defense_3_second_and_traveling   | 2021-22        | 49317           | 5.2%                | 7826        | 6.4%                | 0.620   | 0.133         | 14.3%             | 2.246       | 22.4%                |
| exclude_defense_3_second_and_traveling   | 2022-23        | 49317           | 5.2%                | 10119       | 4.9%                | 0.663   | 0.135         | 12.7%             | 2.588       | 25.9%                |
| exclude_defense_3_second_and_traveling   | 2023-24        | 49317           | 5.2%                | 7393        | 4.8%                | 0.638   | 0.130         | 11.9%             | 2.501       | 25.0%                |
| exclude_defense_3_second_and_traveling   | 2024-25        | 49317           | 5.2%                | 6526        | 3.7%                | 0.628   | 0.122         | 10.1%             | 2.764       | 27.6%                |
| exclude_rare_call_types_lt_100           | 2019-20        | 49850           | 6.1%                | 7392        | 6.6%                | 0.647   | 0.149         | 16.6%             | 2.526       | 25.3%                |
| exclude_rare_call_types_lt_100           | 2020-21        | 49850           | 6.1%                | 7209        | 5.7%                | 0.643   | 0.182         | 17.4%             | 3.030       | 30.3%                |
| exclude_rare_call_types_lt_100           | 2021-22        | 49850           | 6.1%                | 8005        | 7.4%                | 0.668   | 0.200         | 23.2%             | 3.149       | 31.5%                |
| exclude_rare_call_types_lt_100           | 2022-23        | 49850           | 6.1%                | 10312       | 5.9%                | 0.717   | 0.204         | 21.8%             | 3.707       | 37.1%                |
| exclude_rare_call_types_lt_100           | 2023-24        | 49850           | 6.1%                | 7442        | 5.9%                | 0.703   | 0.206         | 21.9%             | 3.731       | 37.3%                |
| exclude_rare_call_types_lt_100           | 2024-25        | 49850           | 6.1%                | 6422        | 4.4%                | 0.693   | 0.176         | 17.3%             | 3.910       | 39.1%                |
| exclude_timing_count_judgment            | 2019-20        | 50050           | 6.0%                | 7392        | 6.6%                | 0.640   | 0.145         | 16.1%             | 2.439       | 24.4%                |
| exclude_timing_count_judgment            | 2020-21        | 50050           | 6.0%                | 7225        | 5.7%                | 0.644   | 0.174         | 16.9%             | 2.978       | 29.8%                |
| exclude_timing_count_judgment            | 2021-22        | 50050           | 6.0%                | 8006        | 7.4%                | 0.668   | 0.203         | 23.2%             | 3.150       | 31.5%                |
| exclude_timing_count_judgment            | 2022-23        | 50050           | 6.0%                | 10327       | 5.8%                | 0.714   | 0.201         | 21.1%             | 3.636       | 36.3%                |
| exclude_timing_count_judgment            | 2023-24        | 50050           | 6.0%                | 7487        | 5.7%                | 0.690   | 0.188         | 19.8%             | 3.494       | 34.9%                |
| exclude_timing_count_judgment            | 2024-25        | 50050           | 6.0%                | 6544        | 4.2%                | 0.678   | 0.159         | 15.3%             | 3.612       | 36.1%                |
| exclude_possession_boundary_adjudication | 2019-20        | 47137           | 5.5%                | 7125        | 6.0%                | 0.596   | 0.092         | 11.2%             | 1.875       | 18.7%                |
| exclude_possession_boundary_adjudication | 2020-21        | 47137           | 5.5%                | 6928        | 5.1%                | 0.593   | 0.119         | 11.3%             | 2.225       | 22.2%                |
| exclude_possession_boundary_adjudication | 2021-22        | 47137           | 5.5%                | 7460        | 6.7%                | 0.643   | 0.166         | 18.1%             | 2.716       | 27.2%                |
| exclude_possession_boundary_adjudication | 2022-23        | 47137           | 5.5%                | 9710        | 5.3%                | 0.689   | 0.171         | 17.6%             | 3.346       | 33.5%                |
| exclude_possession_boundary_adjudication | 2023-24        | 47137           | 5.5%                | 6936        | 5.2%                | 0.682   | 0.209         | 17.7%             | 3.401       | 34.0%                |
| exclude_possession_boundary_adjudication | 2024-25        | 47137           | 5.5%                | 5999        | 3.8%                | 0.666   | 0.207         | 13.0%             | 3.411       | 34.1%                |

## Scenario Definitions

- `full_sample`: Full prepared L2M event sample.
- `exclude_defense_3_second`: Exclude `Foul: Defense 3 Second` events.
- `exclude_traveling`: Exclude `Turnover: Traveling` events.
- `exclude_defense_3_second_and_traveling`: Exclude both `Foul: Defense 3 Second` and `Turnover: Traveling`.
- `exclude_rare_call_types_lt_100`: Exclude raw call types with fewer than 100 events.
- `exclude_timing_count_judgment`: Exclude the timing/count structural category.
- `exclude_possession_boundary_adjudication`: Exclude the possession/boundary structural category.

## Interpretation

The full-sample rolling holdout top-decile lift is 3.5x. After excluding defensive three seconds and traveling, mean top-decile lift is 2.4x. After excluding raw call types with fewer than 100 events, mean top-decile lift is 3.3x. Use these checks to distinguish a broad structural-risk result from a result driven by one or two high-risk call labels.
