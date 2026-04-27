# Post-Event L2M Bad-Call Risk Model

## Rolling Season Holdout

- Events available: **51,130**
- Seasons available: **2018-19 to 2024-25**
- Holdout seasons evaluated: **6**

| holdout_season | train_seasons      | train_events | test_events | test_incorrect | baseline_error_rate | roc_auc | avg_precision | top_10_error_rate | top_10_lift | top_10_error_capture |
| -------------- | ------------------ | ------------ | ----------- | -------------- | ------------------- | ------- | ------------- | ----------------- | ----------- | -------------------- |
| 2019-20        | 2018-19            | 3123         | 7514        | 511            | 6.8%                | 0.654   | 0.158         | 18.6%             | 2.741       | 27.4%                |
| 2020-21        | 2018-19 to 2019-20 | 10637        | 7345        | 435            | 5.9%                | 0.656   | 0.195         | 19.1%             | 3.221       | 32.2%                |
| 2021-22        | 2018-19 to 2020-21 | 17982        | 8171        | 626            | 7.7%                | 0.679   | 0.218         | 26.3%             | 3.435       | 34.3%                |
| 2022-23        | 2018-19 to 2021-22 | 26153        | 10591       | 656            | 6.2%                | 0.728   | 0.224         | 24.4%             | 3.933       | 39.3%                |
| 2023-24        | 2018-19 to 2022-23 | 36744        | 7678        | 462            | 6.0%                | 0.708   | 0.226         | 23.5%             | 3.900       | 39.0%                |
| 2024-25        | 2018-19 to 2023-24 | 44422        | 6708        | 305            | 4.5%                | 0.697   | 0.205         | 18.2%             | 4.005       | 40.0%                |

## Interpretation

The Sloan-relevant test is whether the top structural-risk decile is consistently above baseline in future seasons. Mean top-decile lift across evaluated holdouts was 3.5x.
