# H1b Challenge Overturn Analysis

## Headline

- Challenge events analyzed: **4,294**
- Baseline overturn rate: **67.3%**
- Primary model: **pooled logit without crew-chief effects**
- Back-to-back coefficient: **0.0827**
- Back-to-back odds ratio: **1.0862**
- Back-to-back p-value: **0.5277**
- Decision: **do not scale H1b yet: treat as null/inconclusive and pivot if needed**

## Back-To-Back Split

| back_to_back | challenges | overturn_rate |
| ------------ | ---------- | ------------- |
| 0            | 3932       | 67.2%         |
| 1            | 362        | 68.0%         |

## Days Rest Split

| days_rest_bucket | challenges | overturn_rate |
| ---------------- | ---------- | ------------- |
| 1                | 362        | 68.0%         |
| 2                | 1911       | 66.6%         |
| 3+               | 2007       | 68.0%         |
| unknown          | 14         | 57.1%         |

## Model Notes

Mixed and fixed-effects models failed, so the fallback pooled logit was used. Last fixed-effects error: Singular matrix

## Decision Rule

Scale to Phase 2 only if the back-to-back absolute effect is at least 3 percentage points and p < 0.05. Otherwise treat H1b as a cheap null or inconclusive screen and pivot to pace/Q4 or L2M only if there is a separate reason to continue.
