# L2M Error Workload Analysis

## Headline

- L2M games analyzed: **2,514**
- L2M events reviewed: **51,384**
- L2M incorrect decisions: **3,214**
- Baseline L2M error rate: **6.3%**
- Primary travel model: **binomial GLM with crew-chief fixed effects (travel miles last 7 days)**
- Travel miles coefficient, per 1,000 miles in previous 7 days: **-0.0425**
- Travel miles odds ratio, per 1,000 miles: **0.9583**
- Travel miles p-value: **0.2572**
- Immediate previous-game miles p-value: **0.8461**
- Time-zones-crossed p-value: **0.2841**
- Back-to-back comparison p-value: **0.4655**
- Decision: **travel miles do not explain L2M errors in this sample**

## L2M Travel Split

| travel_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| ------------- | ----- | --------------- | ---------------- | -------------- |
| 0             | 16    | 329             | 30               | 9.1%           |
| 1000-1999     | 384   | 7814            | 508              | 6.5%           |
| 2000-2999     | 656   | 13716           | 895              | 6.5%           |
| 3000+         | 809   | 16211           | 947              | 5.8%           |
| <1000         | 138   | 2859            | 188              | 6.6%           |
| unknown       | 511   | 10455           | 646              | 6.2%           |

## L2M Time-Zone Split

| tz_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| --------- | ----- | --------------- | ---------------- | -------------- |
| 0         | 192   | 3872            | 257              | 6.6%           |
| 1         | 378   | 7932            | 515              | 6.5%           |
| 2         | 446   | 9061            | 575              | 6.3%           |
| 3+        | 987   | 20064           | 1221             | 6.1%           |
| unknown   | 511   | 10455           | 646              | 6.2%           |

## L2M Back-To-Back Split

| back_to_back | games | reviewed_events | incorrect_events | l2m_error_rate |
| ------------ | ----- | --------------- | ---------------- | -------------- |
| 0.0          | 1825  | 37148           | 2325             | 6.3%           |
| 1.0          | 178   | 3781            | 243              | 6.4%           |
| nan          | 511   | 10455           | 646              | 6.2%           |

## L2M Days Rest Split

| days_rest_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| ---------------- | ----- | --------------- | ---------------- | -------------- |
| 1                | 178   | 3781            | 243              | 6.4%           |
| 2                | 864   | 17580           | 1034             | 5.9%           |
| 3+               | 952   | 19403           | 1275             | 6.6%           |
| unknown          | 520   | 10620           | 662              | 6.2%           |

## Challenge Outcomes On L2M Games

| back_to_back | games | challenges | overturned | challenge_overturn_rate |
| ------------ | ----- | ---------- | ---------- | ----------------------- |
| 0.0          | 1825  | 569        | 355        | 62.4%                   |
| 1.0          | 178   | 48         | 35         | 72.9%                   |
| nan          | 511   | 0          | 0          | n/a                     |

## Model Notes

The model is weighted by L2M event count per game and includes crew-chief fixed effects to compare each crew chief against their own baseline where data allows. Predictor tested: travel miles last 7 days.

Immediate previous-game miles model: The model is weighted by L2M event count per game and includes crew-chief fixed effects to compare each crew chief against their own baseline where data allows. Predictor tested: travel miles since previous game.

Time-zone model: The model is weighted by L2M event count per game and includes crew-chief fixed effects to compare each crew chief against their own baseline where data allows. Predictor tested: time zones crossed last 7 days.

Back-to-back comparison model: The model is weighted by L2M event count per game and includes crew-chief fixed effects to compare each crew chief against their own baseline where data allows. Predictor tested: back-to-back.
