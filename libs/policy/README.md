# libs/policy — shared scoring policy

Single-source-of-truth for the NIST AI RMF scoring math used by the
EARP backend. Lives here (not inside the API) so compliance reviewers
can audit policy without reading web-framework code.

## Module

    scoring.py

* `FUNCTION_WEIGHTS` — dict of four weights, each 0.25
* `THRESHOLD_LOW = 80.0`, `THRESHOLD_MED = 60.0`
* `AssessmentInput(govern, map, measure, manage)` dataclass
* `overall_score(inp) -> float`
* `risk_tier(overall) -> "LOW" | "MEDIUM" | "HIGH"`

## Usage

```python
from libs.policy.scoring import AssessmentInput, overall_score, risk_tier

inp = AssessmentInput(govern=85, map=78, measure=72, manage=81)
print(overall_score(inp))   # 79.0
print(risk_tier(79.0))      # 'MEDIUM'
```

## Why a separate library

* **Audit** — reviewers can stare at one short file.
* **Reuse** — dashboards, batch jobs, CLI tools, and the API all share
  the same policy. Change thresholds in one place.
* **Governance** — the CI `ci-contracts.yml` workflow diffs this file
  and requires CODEOWNERS review on changes.
