# L2M Robustness Checks

Rolling season holdout after excluding key call types or structural categories.

## Average By Scenario

| scenario                                 | scenario_events | scenario_error_rate | holdout_seasons | mean_roc_auc | mean_top_10_lift | mean_top_10_error_rate | mean_error_capture |
| ---------------------------------------- | --------------- | ------------------- | --------------- | ------------ | ---------------- | ---------------------- | ------------------ |
| full_sample                              | 51130           | 6.3%                | 6               | 0.687        | 3.539            | 21.7%                  | 35.4%              |
| exclude_defense_3_second                 | 50449           | 5.9%                | 6               | 0.667        | 3.130            | 17.9%                  | 31.3%              |
| exclude_traveling                        | 49998           | 5.6%                | 6               | 0.653        | 2.890            | 15.8%                  | 28.9%              |
| exclude_defense_3_second_and_traveling   | 49317           | 5.2%                | 6               | 0.626        | 2.397            | 12.1%                  | 24.0%              |
| exclude_rare_call_types_lt_100           | 49850           | 6.1%                | 6               | 0.679        | 3.342            | 19.7%                  | 33.4%              |
| exclude_timing_count_judgment            | 50050           | 6.0%                | 6               | 0.672        | 3.215            | 18.7%                  | 32.1%              |
| exclude_possession_boundary_adjudication | 47137           | 5.5%                | 6               | 0.645        | 2.848            | 14.9%                  | 28.5%              |

## By Scenario And Season

| scenario                                 | holdout_season | scenario_events | scenario_error_rate | test_events | baseline_error_rate | roc_auc | avg_precision | top_10_error_rate | top_10_lift | top_10_error_capture |
| ---------------------------------------- | -------------- | --------------- | ------------------- | ----------- | ------------------- | ------- | ------------- | ----------------- | ----------- | -------------------- |
| full_sample                              | 2019-20        | 51130           | 6.3%                | 7514        | 6.8%                | 0.654   | 0.158         | 18.6%             | 2.741       | 27.4%                |
| full_sample                              | 2020-21        | 51130           | 6.3%                | 7345        | 5.9%                | 0.656   | 0.195         | 19.1%             | 3.221       | 32.2%                |
| full_sample                              | 2021-22        | 51130           | 6.3%                | 8171        | 7.7%                | 0.679   | 0.218         | 26.3%             | 3.435       | 34.3%                |
| full_sample                              | 2022-23        | 51130           | 6.3%                | 10591       | 6.2%                | 0.728   | 0.224         | 24.4%             | 3.933       | 39.3%                |
| full_sample                              | 2023-24        | 51130           | 6.3%                | 7678        | 6.0%                | 0.708   | 0.226         | 23.5%             | 3.900       | 39.0%                |
| full_sample                              | 2024-25        | 51130           | 6.3%                | 6708        | 4.5%                | 0.697   | 0.205         | 18.2%             | 4.005       | 40.0%                |
| exclude_defense_3_second                 | 2019-20        | 50449           | 5.9%                | 7440        | 6.6%                | 0.649   | 0.156         | 17.6%             | 2.652       | 26.5%                |
| exclude_defense_3_second                 | 2020-21        | 50449           | 5.9%                | 7293        | 5.8%                | 0.649   | 0.192         | 17.7%             | 3.065       | 30.6%                |
| exclude_defense_3_second                 | 2021-22        | 50449           | 5.9%                | 8025        | 7.2%                | 0.659   | 0.196         | 21.3%             | 2.981       | 29.8%                |
| exclude_defense_3_second                 | 2022-23        | 50449           | 5.9%                | 10376       | 5.6%                | 0.705   | 0.198         | 19.4%             | 3.438       | 34.4%                |
| exclude_defense_3_second                 | 2023-24        | 50449           | 5.9%                | 7571        | 5.4%                | 0.675   | 0.183         | 17.4%             | 3.236       | 32.4%                |
| exclude_defense_3_second                 | 2024-25        | 50449           | 5.9%                | 6655        | 4.1%                | 0.663   | 0.160         | 14.0%             | 3.409       | 34.1%                |
| exclude_traveling                        | 2019-20        | 49998           | 5.6%                | 7355        | 6.2%                | 0.614   | 0.110         | 13.7%             | 2.216       | 22.1%                |
| exclude_traveling                        | 2020-21        | 49998           | 5.6%                | 7195        | 5.2%                | 0.605   | 0.120         | 11.8%             | 2.287       | 22.8%                |
| exclude_traveling                        | 2021-22        | 49998           | 5.6%                | 7972        | 6.9%                | 0.647   | 0.166         | 19.7%             | 2.850       | 28.5%                |
| exclude_traveling                        | 2022-23        | 49998           | 5.6%                | 10334       | 5.5%                | 0.697   | 0.175         | 17.8%             | 3.252       | 32.5%                |
| exclude_traveling                        | 2023-24        | 49998           | 5.6%                | 7500        | 5.4%                | 0.682   | 0.206         | 17.9%             | 3.300       | 33.0%                |
| exclude_traveling                        | 2024-25        | 49998           | 5.6%                | 6579        | 4.1%                | 0.673   | 0.211         | 14.2%             | 3.436       | 34.3%                |
| exclude_defense_3_second_and_traveling   | 2019-20        | 49317           | 5.2%                | 7281        | 6.0%                | 0.607   | 0.105         | 12.4%             | 2.050       | 20.5%                |
| exclude_defense_3_second_and_traveling   | 2020-21        | 49317           | 5.2%                | 7143        | 5.0%                | 0.595   | 0.112         | 10.9%             | 2.180       | 21.8%                |
| exclude_defense_3_second_and_traveling   | 2021-22        | 49317           | 5.2%                | 7826        | 6.4%                | 0.619   | 0.132         | 14.3%             | 2.246       | 22.4%                |
| exclude_defense_3_second_and_traveling   | 2022-23        | 49317           | 5.2%                | 10119       | 4.9%                | 0.663   | 0.134         | 12.9%             | 2.629       | 26.3%                |
| exclude_defense_3_second_and_traveling   | 2023-24        | 49317           | 5.2%                | 7393        | 4.8%                | 0.638   | 0.130         | 12.2%             | 2.558       | 25.6%                |
| exclude_defense_3_second_and_traveling   | 2024-25        | 49317           | 5.2%                | 6526        | 3.7%                | 0.632   | 0.121         | 10.0%             | 2.722       | 27.2%                |
| exclude_rare_call_types_lt_100           | 2019-20        | 49850           | 6.1%                | 7392        | 6.6%                | 0.647   | 0.149         | 16.6%             | 2.526       | 25.3%                |
| exclude_rare_call_types_lt_100           | 2020-21        | 49850           | 6.1%                | 7209        | 5.7%                | 0.643   | 0.182         | 17.4%             | 3.030       | 30.3%                |
| exclude_rare_call_types_lt_100           | 2021-22        | 49850           | 6.1%                | 8005        | 7.4%                | 0.668   | 0.200         | 23.2%             | 3.149       | 31.5%                |
| exclude_rare_call_types_lt_100           | 2022-23        | 49850           | 6.1%                | 10312       | 5.9%                | 0.717   | 0.204         | 21.8%             | 3.707       | 37.1%                |
| exclude_rare_call_types_lt_100           | 2023-24        | 49850           | 6.1%                | 7442        | 5.9%                | 0.703   | 0.206         | 21.9%             | 3.731       | 37.3%                |
| exclude_rare_call_types_lt_100           | 2024-25        | 49850           | 6.1%                | 6422        | 4.4%                | 0.693   | 0.176         | 17.3%             | 3.910       | 39.1%                |
| exclude_timing_count_judgment            | 2019-20        | 50050           | 6.0%                | 7392        | 6.6%                | 0.640   | 0.145         | 16.1%             | 2.439       | 24.4%                |
| exclude_timing_count_judgment            | 2020-21        | 50050           | 6.0%                | 7225        | 5.7%                | 0.644   | 0.174         | 16.9%             | 2.978       | 29.8%                |
| exclude_timing_count_judgment            | 2021-22        | 50050           | 6.0%                | 8006        | 7.4%                | 0.667   | 0.201         | 23.1%             | 3.133       | 31.3%                |
| exclude_timing_count_judgment            | 2022-23        | 50050           | 6.0%                | 10327       | 5.8%                | 0.714   | 0.201         | 21.1%             | 3.636       | 36.3%                |
| exclude_timing_count_judgment            | 2023-24        | 50050           | 6.0%                | 7487        | 5.7%                | 0.690   | 0.187         | 20.2%             | 3.565       | 35.6%                |
| exclude_timing_count_judgment            | 2024-25        | 50050           | 6.0%                | 6544        | 4.2%                | 0.677   | 0.159         | 15.0%             | 3.540       | 35.4%                |
| exclude_possession_boundary_adjudication | 2019-20        | 47137           | 5.5%                | 7125        | 6.0%                | 0.598   | 0.092         | 11.4%             | 1.898       | 19.0%                |
| exclude_possession_boundary_adjudication | 2020-21        | 47137           | 5.5%                | 6928        | 5.1%                | 0.593   | 0.119         | 11.3%             | 2.225       | 22.2%                |
| exclude_possession_boundary_adjudication | 2021-22        | 47137           | 5.5%                | 7460        | 6.7%                | 0.643   | 0.165         | 18.4%             | 2.757       | 27.6%                |
| exclude_possession_boundary_adjudication | 2022-23        | 47137           | 5.5%                | 9710        | 5.3%                | 0.689   | 0.170         | 17.4%             | 3.307       | 33.1%                |
| exclude_possession_boundary_adjudication | 2023-24        | 47137           | 5.5%                | 6936        | 5.2%                | 0.682   | 0.212         | 17.7%             | 3.401       | 34.0%                |
| exclude_possession_boundary_adjudication | 2024-25        | 47137           | 5.5%                | 5999        | 3.8%                | 0.666   | 0.207         | 13.4%             | 3.499       | 34.9%                |

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
