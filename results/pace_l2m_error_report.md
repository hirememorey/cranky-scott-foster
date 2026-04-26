# Pace / In-Game Load L2M Analysis

## Headline

- L2M games analyzed: **397**
- L2M events reviewed: **6,673**
- L2M incorrect decisions: **304**
- Baseline L2M error rate: **4.6%**
- Full-game pace p-value: **0.2531**
- Q4 pre-L2M action density p-value: **0.1966**
- L2M action density p-value: **0.2886**
- Decision: **pace/load proxies do not explain L2M errors in this sample**

## Full-Game Pace Split

| pace_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| ----------- | ----- | --------------- | ---------------- | -------------- |
| pace_high   | 133   | 2236            | 91               | 4.1%           |
| pace_low    | 132   | 2289            | 117              | 5.1%           |
| pace_mid    | 132   | 2148            | 96               | 4.5%           |

## Q4 Pre-L2M Load Split

| q4_load_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| -------------- | ----- | --------------- | ---------------- | -------------- |
| q4_load_high   | 133   | 2162            | 91               | 4.2%           |
| q4_load_low    | 132   | 2224            | 111              | 5.0%           |
| q4_load_mid    | 132   | 2287            | 102              | 4.5%           |

## L2M Action Density Split

| l2m_load_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| --------------- | ----- | --------------- | ---------------- | -------------- |
| l2m_load_high   | 133   | 2441            | 103              | 4.2%           |
| l2m_load_low    | 132   | 2049            | 90               | 4.4%           |
| l2m_load_mid    | 132   | 2183            | 111              | 5.1%           |

## Model Notes

estimated full-game pace per 5 possessions: coef=-0.0762, OR=0.9267, p=0.2531. Crew-chief fixed effects; weighted by L2M event count.

Q4 pre-L2M actions per minute: coef=-0.0729, OR=0.9297, p=0.1966. Crew-chief fixed effects; weighted by L2M event count.

L2M actions per minute: coef=-0.0147, OR=0.9854, p=0.2886. Crew-chief fixed effects; weighted by L2M event count.
