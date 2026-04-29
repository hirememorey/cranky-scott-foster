# Crew Chief Pipeline vs. Structural Officiating Risk (L2M)

This report joins **crew chief tenure** (games as chief before this game in our assignment DB), **trio familiarity** (prior games with the same three officials), and the **MRT taxonomy** (`monitoring_type`) for Last Two Minute events.

## Data limits

- L2M is a **league audit subset** (close games, reviewed events), not all whistles.
- Crew chief identity comes from **assignment scrape order** (crew chief listed first). See `scripts/collect_officials.py`.
- Experience is **games as crew chief observed in this database** (RS + playoffs when collected), not league-internal tenure.
- **Selection**: senior chiefs receive harder assignments; interpret heterogeneity as descriptive.

## Assignment coverage vs. L2M games

Full crew pipeline requires exactly one row each for `crew_chief`, `official_2`, and `official_3`. See also `scripts/report_l2m_assignment_coverage.py` for gap CSV.

| season  | l2m_games | with_any_assignment | with_chief_row | full_trio | pct_full_trio | pct_with_chief |
| ------- | --------- | ------------------- | -------------- | --------- | ------------- | -------------- |
| 2018-19 | 170       | 170                 | 170            | 170       | 100.0         | 100.0          |
| 2019-20 | 385       | 385                 | 385            | 385       | 100.0         | 100.0          |
| 2020-21 | 402       | 402                 | 402            | 402       | 100.0         | 100.0          |
| 2021-22 | 435       | 435                 | 435            | 435       | 100.0         | 100.0          |
| 2022-23 | 470       | 470                 | 470            | 470       | 100.0         | 100.0          |
| 2023-24 | 411       | 411                 | 411            | 411       | 100.0         | 100.0          |
| 2024-25 | 428       | 428                 | 428            | 428       | 100.0         | 100.0          |

### Regular season vs playoffs (L2M games)

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

- L2M games **without** a complete trio in assignments: **0**

- Events with assigned experience tier: **55,490** (dropped 0 without full crew join).

## Experience tier × taxonomy (error rates)

Pre-defined tiers: `<75` chief games, `75–299`, `≥300` prior games as crew chief.

| experience_tier           | monitoring_type        | n     | incorrect | error_rate | wilson_low | wilson_high |
| ------------------------- | ---------------------- | ----- | --------- | ---------- | ---------- | ----------- |
| tier_1_lt75_chief_games   | focal_discrete         | 27196 | 1295      | 4.8%       | 0.0451     | 0.0502      |
| tier_1_lt75_chief_games   | ambient_continuous     | 4134  | 391       | 9.5%       | 0.0860     | 0.1039      |
| tier_1_lt75_chief_games   | focal_continuous       | 2392  | 421       | 17.6%      | 0.1613     | 0.1918      |
| tier_1_lt75_chief_games   | temporal_discrete      | 675   | 128       | 19.0%      | 0.1618     | 0.2209      |
| tier_1_lt75_chief_games   | administrative_process | 265   | 17        | 6.4%       | 0.0404     | 0.1003      |
| tier_2_75_299_chief_games | focal_discrete         | 15676 | 591       | 3.8%       | 0.0348     | 0.0408      |
| tier_2_75_299_chief_games | ambient_continuous     | 2335  | 232       | 9.9%       | 0.0879     | 0.1122      |
| tier_2_75_299_chief_games | focal_continuous       | 1911  | 278       | 14.5%      | 0.1304     | 0.1620      |
| tier_2_75_299_chief_games | temporal_discrete      | 482   | 106       | 22.0%      | 0.1852     | 0.2590      |
| tier_2_75_299_chief_games | administrative_process | 278   | 15        | 5.4%       | 0.0330     | 0.0871      |
| tier_3_ge300_chief_games  | focal_discrete         | 118   | 7         | 5.9%       | 0.0290     | 0.1174      |
| tier_3_ge300_chief_games  | ambient_continuous     | 13    | 1         | 7.7%       | 0.0137     | 0.3331      |
| tier_3_ge300_chief_games  | focal_continuous       | 12    | 2         | 16.7%      | 0.0470     | 0.4480      |
| tier_3_ge300_chief_games  | temporal_discrete      | 2     | 0         | 0.0%       | 0.0000     | 0.6576      |
| tier_3_ge300_chief_games  | administrative_process | 1     | 0         | 0.0%       | 0.0000     | 0.7935      |

## Familiarity (season-to-date trio count) × taxonomy

| familiarity_bucket_season | monitoring_type        | n     | incorrect | error_rate | wilson_low | wilson_high |
| ------------------------- | ---------------------- | ----- | --------- | ---------- | ---------- | ----------- |
| first_time_trio           | focal_discrete         | 41539 | 1837      | 4.4%       | 0.0423     | 0.0462      |
| first_time_trio           | ambient_continuous     | 6308  | 605       | 9.6%       | 0.0889     | 0.1034      |
| first_time_trio           | focal_continuous       | 4189  | 682       | 16.3%      | 0.1519     | 0.1743      |
| first_time_trio           | temporal_discrete      | 1105  | 224       | 20.3%      | 0.1801     | 0.2274      |
| first_time_trio           | administrative_process | 533   | 32        | 6.0%       | 0.0428     | 0.0835      |
| low_1_to_5                | focal_discrete         | 1451  | 56        | 3.9%       | 0.0298     | 0.0498      |
| low_1_to_5                | ambient_continuous     | 174   | 19        | 10.9%      | 0.0710     | 0.1642      |
| low_1_to_5                | focal_continuous       | 126   | 19        | 15.1%      | 0.0987     | 0.2235      |
| low_1_to_5                | temporal_discrete      | 54    | 10        | 18.5%      | 0.1038     | 0.3084      |
| low_1_to_5                | administrative_process | 11    | 0         | 0.0%       | 0.0000     | 0.2588      |

## Regular season vs. playoffs

| is_playoff | monitoring_type        | n     | incorrect | error_rate | wilson_low | wilson_high |
| ---------- | ---------------------- | ----- | --------- | ---------- | ---------- | ----------- |
| 0          | focal_discrete         | 39645 | 1757      | 4.4%       | 0.0423     | 0.0464      |
| 0          | ambient_continuous     | 5907  | 568       | 9.6%       | 0.0889     | 0.1039      |
| 0          | focal_continuous       | 3993  | 644       | 16.1%      | 0.1502     | 0.1730      |
| 0          | temporal_discrete      | 1080  | 214       | 19.8%      | 0.1755     | 0.2230      |
| 0          | administrative_process | 505   | 31        | 6.1%       | 0.0436     | 0.0858      |
| 1          | focal_discrete         | 3345  | 136       | 4.1%       | 0.0345     | 0.0479      |
| 1          | ambient_continuous     | 575   | 56        | 9.7%       | 0.0758     | 0.1244      |
| 1          | focal_continuous       | 322   | 57        | 17.7%      | 0.1392     | 0.2224      |
| 1          | temporal_discrete      | 79    | 20        | 25.3%      | 0.1703     | 0.3589      |
| 1          | administrative_process | 39    | 1         | 2.6%       | 0.0045     | 0.1318      |

- Events (RS vs playoff): **51,130** vs **4,360** (playoff requires `--include-playoffs` L2M + assignments).

## Logistic models (exploratory)

Reference category: focal/discrete × tier 1. Clustering by game not shown (MLE only).


```
                           Logit Regression Results                           
==============================================================================
Dep. Variable:              incorrect   No. Observations:                55490
Model:                          Logit   Df Residuals:                    55483
Method:                           MLE   Df Model:                            6
Date:                Wed, 29 Apr 2026   Pseudo R-squ.:                 0.04535
Time:                        09:00:35   Log-Likelihood:                -12426.
converged:                       True   LL-Null:                       -13016.
Covariance Type:            nonrobust   LLR p-value:                7.307e-252
===================================================================================================================
                                                      coef    std err          z      P>|z|      [0.025      0.975]
-------------------------------------------------------------------------------------------------------------------
Intercept                                          -2.6941      0.183    -14.713      0.000      -3.053      -2.335
C(monitoring_type)[T.ambient_continuous]            0.5096      0.187      2.723      0.006       0.143       0.876
C(monitoring_type)[T.focal_continuous]              1.1223      0.187      6.005      0.000       0.756       1.489
C(monitoring_type)[T.focal_discrete]               -0.3284      0.184     -1.786      0.074      -0.689       0.032
C(monitoring_type)[T.temporal_discrete]             1.3839      0.196      7.045      0.000       0.999       1.769
C(experience_tier)[T.tier_2_75_299_chief_games]    -0.1593      0.037     -4.272      0.000      -0.232      -0.086
C(experience_tier)[T.tier_3_ge300_chief_games]      0.0748      0.333      0.224      0.822      -0.578       0.728
===================================================================================================================
```


```
                           Logit Regression Results                           
==============================================================================
Dep. Variable:              incorrect   No. Observations:                55490
Model:                          Logit   Df Residuals:                    55475
Method:                           MLE   Df Model:                           14
Date:                Wed, 29 Apr 2026   Pseudo R-squ.:                 0.04598
Time:                        09:00:35   Log-Likelihood:                -12418.
converged:                      False   LL-Null:                       -13016.
Covariance Type:            nonrobust   LLR p-value:                7.533e-247
============================================================================================================================================================
                                                                                               coef    std err          z      P>|z|      [0.025      0.975]
------------------------------------------------------------------------------------------------------------------------------------------------------------
Intercept                                                                                   -2.6802      0.251    -10.690      0.000      -3.172      -2.189
C(monitoring_type)[T.ambient_continuous]                                                     0.4213      0.256      1.644      0.100      -0.081       0.924
C(monitoring_type)[T.focal_continuous]                                                       1.1366      0.256      4.433      0.000       0.634       1.639
C(monitoring_type)[T.focal_discrete]                                                        -0.3156      0.252     -1.251      0.211      -0.810       0.179
C(monitoring_type)[T.temporal_discrete]                                                      1.2278      0.269      4.560      0.000       0.700       1.756
C(experience_tier)[T.tier_2_75_299_chief_games]                                             -0.1839      0.365     -0.504      0.615      -0.900       0.532
C(experience_tier)[T.tier_3_ge300_chief_games]                                             -20.0873   8.79e+04     -0.000      1.000   -1.72e+05    1.72e+05
C(monitoring_type)[T.ambient_continuous]:C(experience_tier)[T.tier_2_75_299_chief_games]     0.2384      0.375      0.635      0.525      -0.497       0.974
C(monitoring_type)[T.focal_continuous]:C(experience_tier)[T.tier_2_75_299_chief_games]      -0.0430      0.375     -0.115      0.909      -0.777       0.691
C(monitoring_type)[T.focal_discrete]:C(experience_tier)[T.tier_2_75_299_chief_games]        -0.0600      0.369     -0.163      0.871      -0.782       0.663
C(monitoring_type)[T.temporal_discrete]:C(experience_tier)[T.tier_2_75_299_chief_games]      0.3702      0.394      0.940      0.347      -0.402       1.142
C(monitoring_type)[T.ambient_continuous]:C(experience_tier)[T.tier_3_ge300_chief_games]     19.8613   8.79e+04      0.000      1.000   -1.72e+05    1.72e+05
C(monitoring_type)[T.focal_continuous]:C(experience_tier)[T.tier_3_ge300_chief_games]       20.0215   8.79e+04      0.000      1.000   -1.72e+05    1.72e+05
C(monitoring_type)[T.focal_discrete]:C(experience_tier)[T.tier_3_ge300_chief_games]         20.3194   8.79e+04      0.000      1.000   -1.72e+05    1.72e+05
C(monitoring_type)[T.temporal_discrete]:C(experience_tier)[T.tier_3_ge300_chief_games]      -8.1404   1.97e+06  -4.13e-06      1.000   -3.86e+06    3.86e+06
============================================================================================================================================================
```

- LR test interaction vs main (approx): chi^2 = 16.36, df = 8


```
                           Logit Regression Results                           
==============================================================================
Dep. Variable:              incorrect   No. Observations:                55490
Model:                          Logit   Df Residuals:                    55480
Method:                           MLE   Df Model:                            9
Date:                Wed, 29 Apr 2026   Pseudo R-squ.:                 0.04475
Time:                        09:00:35   Log-Likelihood:                -12434.
converged:                      False   LL-Null:                       -13016.
Covariance Type:            nonrobust   LLR p-value:                4.269e-245
=======================================================================================================================================================
                                                                                          coef    std err          z      P>|z|      [0.025      0.975]
-------------------------------------------------------------------------------------------------------------------------------------------------------
Intercept                                                                              -2.7509      0.182    -15.087      0.000      -3.108      -2.394
C(monitoring_type)[T.ambient_continuous]                                                0.5074      0.187      2.709      0.007       0.140       0.874
C(monitoring_type)[T.focal_continuous]                                                  1.1134      0.187      5.952      0.000       0.747       1.480
C(monitoring_type)[T.focal_discrete]                                                   -0.3224      0.184     -1.753      0.080      -0.683       0.038
C(monitoring_type)[T.temporal_discrete]                                                 1.3815      0.197      7.009      0.000       0.995       1.768
C(familiarity_bucket_season)[T.low_1_to_5]                                            -12.2654    549.586     -0.022      0.982   -1089.434    1064.903
C(monitoring_type)[T.ambient_continuous]:C(familiarity_bucket_season)[T.low_1_to_5]    12.4099    549.586      0.023      0.982   -1064.759    1089.578
C(monitoring_type)[T.focal_continuous]:C(familiarity_bucket_season)[T.low_1_to_5]      12.1745    549.586      0.022      0.982   -1064.994    1089.343
C(monitoring_type)[T.focal_discrete]:C(familiarity_bucket_season)[T.low_1_to_5]        12.1233    549.586      0.022      0.982   -1065.045    1089.292
C(monitoring_type)[T.temporal_discrete]:C(familiarity_bucket_season)[T.low_1_to_5]     12.1532    549.586      0.022      0.982   -1065.015    1089.322
=======================================================================================================================================================
```

## IC vs INC asymmetry (exploratory)

Among **calls** (CC/IC): IC rate; among **non-calls** (CNC/INC): INC rate. League grading difficulty differs by play type—interpret cautiously.

### Calls (CC + IC)
| experience_tier           | ic  | n_calls | ic_rate_given_call   |
| ------------------------- | --- | ------- | -------------------- |
| tier_1_lt75_chief_games   | 327 | 7777    | 0.04204706184904205  |
| tier_2_75_299_chief_games | 183 | 5054    | 0.036208943411159475 |
| tier_3_ge300_chief_games  | 2   | 31      | 0.06451612903225806  |

### Non-calls (CNC + INC)
| experience_tier           | inc  | n_nc  | inc_rate_given_noncall_review |
| ------------------------- | ---- | ----- | ----------------------------- |
| tier_1_lt75_chief_games   | 1925 | 26885 | 0.07160126464571322           |
| tier_2_75_299_chief_games | 1039 | 15628 | 0.06648323521883798           |
| tier_3_ge300_chief_games  | 8    | 115   | 0.06956521739130435           |

## Pipeline demographics (tier counts by season)

| season  | experience_tier           | chiefs |
| ------- | ------------------------- | ------ |
| 2020-21 | tier_1_lt75_chief_games   | 78     |
| 2021-22 | tier_1_lt75_chief_games   | 49     |
| 2021-22 | tier_2_75_299_chief_games | 11     |
| 2022-23 | tier_1_lt75_chief_games   | 36     |
| 2022-23 | tier_2_75_299_chief_games | 20     |
| 2023-24 | tier_1_lt75_chief_games   | 33     |
| 2023-24 | tier_2_75_299_chief_games | 26     |
| 2024-25 | tier_1_lt75_chief_games   | 29     |
| 2024-25 | tier_2_75_299_chief_games | 30     |
| 2024-25 | tier_3_ge300_chief_games  | 2      |

## Interpretation notes

- **Positive interaction** between high attention-load taxonomy buckets and lower experience would align with the Dowsett "pipeline" narrative; nulls are informative given selection bias.
- Use **Wilson** intervals when comparing small playoff slices.
