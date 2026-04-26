# L2M Error Workload Analysis

## Headline

- L2M games analyzed: **399**
- L2M events reviewed: **6,710**
- L2M incorrect decisions: **305**
- Baseline L2M error rate: **4.5%**
- Primary travel model: **binomial GLM with crew-chief fixed effects (travel miles last 7 days)**
- Travel miles coefficient, per 1,000 miles in previous 7 days: **-0.0865**
- Travel miles odds ratio, per 1,000 miles: **0.9171**
- Travel miles p-value: **0.4693**
- Immediate previous-game miles p-value: **0.5989**
- Time-zones-crossed p-value: **0.5856**
- Back-to-back comparison p-value: **0.5563**
- Decision: **travel miles do not explain L2M errors in this sample**

## L2M Travel Split

| travel_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| ------------- | ----- | --------------- | ---------------- | -------------- |
| 0             | 1     | 14              | 1                | 7.1%           |
| 1000-1999     | 82    | 1454            | 77               | 5.3%           |
| 2000-2999     | 118   | 1999            | 89               | 4.5%           |
| 3000+         | 175   | 2826            | 116              | 4.1%           |
| <1000         | 21    | 380             | 21               | 5.5%           |
| unknown       | 2     | 37              | 1                | 2.7%           |

## L2M Time-Zone Split

| tz_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| --------- | ----- | --------------- | ---------------- | -------------- |
| 0         | 36    | 588             | 30               | 5.1%           |
| 1         | 80    | 1414            | 73               | 5.2%           |
| 2         | 86    | 1536            | 65               | 4.2%           |
| 3+        | 195   | 3135            | 136              | 4.3%           |
| unknown   | 2     | 37              | 1                | 2.7%           |

## L2M Back-To-Back Split

| back_to_back | games | reviewed_events | incorrect_events | l2m_error_rate |
| ------------ | ----- | --------------- | ---------------- | -------------- |
| 0.0          | 364   | 6129            | 280              | 4.6%           |
| 1.0          | 33    | 544             | 24               | 4.4%           |
| nan          | 2     | 37              | 1                | 2.7%           |

## L2M Days Rest Split

| days_rest_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| ---------------- | ----- | --------------- | ---------------- | -------------- |
| 1                | 33    | 544             | 24               | 4.4%           |
| 2                | 179   | 2931            | 126              | 4.3%           |
| 3+               | 184   | 3184            | 153              | 4.8%           |
| unknown          | 3     | 51              | 2                | 3.9%           |

## Challenge Outcomes On L2M Games

| back_to_back | games | challenges | overturned | challenge_overturn_rate |
| ------------ | ----- | ---------- | ---------- | ----------------------- |
| 0.0          | 364   | 569        | 355        | 62.4%                   |
| 1.0          | 33    | 48         | 35         | 72.9%                   |
| nan          | 2     | 0          | 0          | n/a                     |

## Model Notes

The model is weighted by L2M event count per game and includes crew-chief fixed effects to compare each crew chief against their own baseline where data allows. Predictor tested: travel miles last 7 days.

Immediate previous-game miles model: The model is weighted by L2M event count per game and includes crew-chief fixed effects to compare each crew chief against their own baseline where data allows. Predictor tested: travel miles since previous game.

Time-zone model: The model is weighted by L2M event count per game and includes crew-chief fixed effects to compare each crew chief against their own baseline where data allows. Predictor tested: time zones crossed last 7 days.

Back-to-back comparison model: The model is weighted by L2M event count per game and includes crew-chief fixed effects to compare each crew chief against their own baseline where data allows. Predictor tested: back-to-back.
