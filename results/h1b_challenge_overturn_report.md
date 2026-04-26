# H1b Challenge Overturn Analysis

## Headline

- Challenge events analyzed: **1,636**
- Baseline overturn rate: **66.1%**
- Primary model: **Bayesian mixed logit with crew-chief random intercepts**
- Back-to-back coefficient: **-0.0631**
- Back-to-back odds ratio: **0.9389**
- Back-to-back p-value: **0.6197**
- Decision: **do not scale H1b yet: treat as null/inconclusive and pivot if needed**

## Back-To-Back Split

| back_to_back | challenges | overturn_rate |
| ------------ | ---------- | ------------- |
| 0            | 1508       | 66.0%         |
| 1            | 128        | 67.2%         |

## Days Rest Split

| days_rest_bucket | challenges | overturn_rate |
| ---------------- | ---------- | ------------- |
| 1                | 128        | 67.2%         |
| 2                | 744        | 68.4%         |
| 3+               | 759        | 63.6%         |
| unknown          | 5          | 60.0%         |

## Model Notes

Statsmodels BinomialBayesMixedGLM estimates the planned (1|crew_chief) random intercept. The p-value is reported from a crew-chief fixed-effects logit because the Bayesian mixed model does not expose frequentist p-values.

## Decision Rule

Scale to Phase 2 only if the back-to-back absolute effect is at least 3 percentage points and p < 0.05. Otherwise treat H1b as a cheap null or inconclusive screen and pivot to pace/Q4 or L2M only if there is a separate reason to continue.
