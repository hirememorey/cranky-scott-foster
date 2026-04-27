# Pace / In-Game Load L2M Analysis

## Headline

- L2M games analyzed: **2,508**
- L2M events reviewed: **51,237**
- L2M incorrect decisions: **3,204**
- Baseline L2M error rate: **6.3%**
- Full-game pace p-value: **0.2816**
- Q4 pre-L2M action density p-value: **0.7966**
- L2M action density p-value: **0.3811**
- Decision: **pace/load proxies do not explain L2M errors in this sample**

## Full-Game Pace Split

| pace_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| ----------- | ----- | --------------- | ---------------- | -------------- |
| pace_high   | 836   | 17405           | 1052             | 6.0%           |
| pace_low    | 836   | 16895           | 1089             | 6.4%           |
| pace_mid    | 836   | 16937           | 1063             | 6.3%           |

## Q4 Pre-L2M Load Split

| q4_load_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| -------------- | ----- | --------------- | ---------------- | -------------- |
| q4_load_high   | 836   | 17217           | 1076             | 6.2%           |
| q4_load_low    | 836   | 16876           | 1081             | 6.4%           |
| q4_load_mid    | 836   | 17144           | 1047             | 6.1%           |

## L2M Action Density Split

| l2m_load_bucket | games | reviewed_events | incorrect_events | l2m_error_rate |
| --------------- | ----- | --------------- | ---------------- | -------------- |
| l2m_load_high   | 836   | 17587           | 1083             | 6.2%           |
| l2m_load_low    | 836   | 15799           | 993              | 6.3%           |
| l2m_load_mid    | 836   | 17851           | 1128             | 6.3%           |

## Model Notes

estimated full-game pace per 5 possessions: coef=-0.0236, OR=0.9767, p=0.2816. Crew-chief fixed effects; weighted by L2M event count.

Q4 pre-L2M actions per minute: coef=-0.0049, OR=0.9951, p=0.7966. Crew-chief fixed effects; weighted by L2M event count.

L2M actions per minute: coef=-0.0039, OR=0.9961, p=0.3811. Crew-chief fixed effects; weighted by L2M event count.
