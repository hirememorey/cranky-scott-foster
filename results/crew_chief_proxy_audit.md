# Crew-Chief Proxy Audit

Source: https://official.nba.com/referee-assignments/

## Headline

- Games audited: **3**
- Lowest-jersey proxy matched NBA-listed crew chief: **1 of 3**
- Proxy match rate: **33.3%**

## Game-Level Check

| game                   | crew_chief     | referee           | umpire           | crew_chief_jersey | referee_jersey | umpire_jersey | lowest_jersey_proxy | proxy_matches_crew_chief |
| ---------------------- | -------------- | ----------------- | ---------------- | ----------------- | -------------- | ------------- | ------------------- | ------------------------ |
| Philadelphia @ Boston  | James Williams | Kevin Scott       | Brian Forte      | 60                | 24             | 45            | Kevin Scott         | False                    |
| Atlanta @ New York     | Josh Tiven     | Courtney Kirkland | Justin Van Duyne | 58                | 61             | 64            | Josh Tiven          | True                     |
| Portland @ San Antonio | Marc Davis     | Nick Buchert      | Ray Acosta       | 8                 | 3              | 54            | Nick Buchert        | False                    |

## Interpretation

The NBA assignments page is an explicit role source. If the lowest-jersey proxy does not match this page, historical rows derived only from jersey sorting should remain unverified and should not support public crew-chief claims.
