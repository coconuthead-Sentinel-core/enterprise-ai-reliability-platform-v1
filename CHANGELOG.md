# Changelog

All notable changes to the Enterprise AI Reliability Platform (EARP) will be
documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

**Sprint 3 — Policy Gate Evaluation (Epic E3, story E3-S2):**
- `POST /assessments` now runs the policy gate against its own NIST-RMF
  scores and persists the decision alongside the assessment record, so
  `risk_tier` and the gate outcome never drift out of sync.
- `database.Assessment` extended with two nullable columns:
  - `gate_decision` (`allow` / `warn` / `block`),
  - `gate_reasons_json` (serialized `PolicyReason` list).
  A helper `.gate_reasons` property deserializes the JSON so Pydantic's
  `from_attributes` can materialize the list without extra glue.
- `AssessmentOutput` schema extended with `gate_decision`
  (`Optional[PolicyDecision]`) and `gate_reasons: List[PolicyReason]`
  (default `[]`). `GET /assessments`, `GET /assessments/{id}`, and the
  201 response of `POST /assessments` all carry the new fields.
- New service helpers `_assessment_score_input()` and
  `gate_assessment()` project the 4-function assessment payload into a
  `ReliabilityScoreInput` (one component per NIST function, weighted
  equally) and run it through `evaluate_policy_gate_from_input()`.
- 34 new integration assertions (section 16) covering:
  - ALLOW: all-90 assessment → LOW tier + `allow` + no block reasons,
  - BLOCK (composite band): all-30 assessment → HIGH tier + `block`
    with `composite_below_warn` reason first,
  - BLOCK (NIST floor): govern=20 / others=95 → MEDIUM tier composite
    but `nist_govern_below_floor` forces overall `block`,
  - `GET /assessments` list and `GET /assessments/{id}` both return
    `gate_decision` + `gate_reasons` on every row,
  - 404 path for a missing assessment still works.
  Suite now runs **218/218**, up from 184/184.

**Sprint 3 — Policy Gate Evaluation (Epic E3, story E3-S1):**
- `POST /policy/evaluate` — run a gate against a reliability score and
  return an `allow` / `warn` / `block` decision with detailed reasons.
- New `policy` router and `app/routers/policy.py` module.
- New Pydantic schemas:
  - `PolicyDecision` enum (`allow` / `warn` / `block`),
  - `PolicySeverity` enum (`info` / `warn` / `block`),
  - `PolicyThresholds` — configurable `allow_min_composite` (default 80),
    `warn_min_composite` (default 60), `min_nist_function_score`
    (default 40) with a validator that enforces warn ≤ allow,
  - `PolicyReason` — machine-readable `code`, human-readable `message`,
    and a `severity`,
  - `PolicyGateInput` / `PolicyGateDecision` request / response models.
- `evaluate_policy_gate()` and `evaluate_policy_gate_from_input()`
  service helpers. Rules fired in this order: composite-band classification
  (allow / warn / block) then per-NIST-function floor. Reasons are
  returned worst-severity-first; a single `block` reason forces the
  overall decision to `block`.
- Epic E3 now reports `in_progress` in `/info/epics` and
  `current_sprint=3` in `/info/sprint`.
- 32 new integration assertions: allow / warn / block happy paths, NIST
  floor trumping a passing composite, custom-threshold override, and
  validation (`warn_min > allow_min` → 422, empty components → 422).
  Suite now runs **184/184**, up from 152/152.

**Sprint 2 — Reliability Scoring Engine (Epic E2, story E2-S3):**
- `GET /reliability/score/history` — persisted score history + trend stats.
  Optional `system_name` filter and `limit` (1–500, default 50).
- `ReliabilityScoreRecord` SQLAlchemy model (`reliability_score_records`
  table, indexed on `system_name` and `created_at`) — stores every
  composite score produced by `POST /reliability/score` and
  `POST /reliability/score/explain`.
- `ScoreTrendStats` response model with `count`, `latest_score`,
  `latest_tier`, `earliest_score`, `earliest_tier`, `rolling_average`,
  `min_score`, `max_score`, `trend_direction` (`improving` /
  `degrading` / `stable` / `insufficient_data`), and a chronological
  list of `TierTransition`s (LOW ↔ MEDIUM ↔ HIGH crossings).
- `reliability_score_history()`, `list_score_history()`, and
  `score_trend_stats()` service helpers.
- Existing POST routes now inject a DB session and persist automatically,
  so history is populated without a separate write call.
- 36 new integration assertions: empty-filter, HIGH→MEDIUM→LOW
  trending, degrading path, stable classification, explain-also-persists,
  global history, `limit` clamping, and `limit` validation. Suite now
  runs **152/152**, up from 116/116.

**Sprint 2 — Reliability Scoring Engine (Epic E2, story E2-S2):**
- `POST /reliability/score/explain` — composite score plus a structured
  explanation object. The response includes:
  - `contributions` — per-component contribution to the composite (absolute
    on the 0-100 scale and percent-of-composite), sorted highest-first,
  - `top_driver` and `top_gap` — the component pulling the score up the
    most vs. the component with the largest improvement opportunity,
  - `tier_gap` — points-to-next-tier-up / points-of-buffer-down against
    the LOW (≥80) and MEDIUM (≥60) thresholds,
  - `weakest_nist_function` / `strongest_nist_function` — derived from the
    per-NIST-function breakdown,
  - `recommendation` — one-sentence plain-English suggestion for the owner.
- `ScoreContribution`, `TierGap`, `ScoreExplanation`, and
  `ReliabilityScoreWithExplanation` Pydantic schemas.
- `explain_reliability_score()` service layered on top of
  `compute_reliability_score()` — no new dependencies.
- 35 new integration assertions for the explanation endpoint (happy path,
  sort invariants, contribution arithmetic, LOW / MEDIUM / HIGH tier-gap
  paths, single-component edge case, validation). Suite now runs
  **116/116**, up from 81/81.

**Sprint 2 — Reliability Scoring Engine (Epic E2, story E2-S1):**
- `POST /reliability/score` — weighted composite reliability score endpoint.
  Accepts a list of `ReliabilityScoreComponent` (name, value 0-1, weight 0-1,
  optional `nist_function`), returns a 0-100 composite, a LOW/MEDIUM/HIGH
  tier, the normalization flag, and a per-NIST-function weighted breakdown.
- `NISTFunction` enum for the four NIST AI RMF 1.0 functions (`govern`,
  `map`, `measure`, `manage`).
- `compute_reliability_score()` service with a pure-Python weighted-average
  implementation and automatic weight normalization.
- 19 new integration assertions for the scoring engine (happy path, NIST
  breakdown, weight normalization, three tier boundaries, three validation
  errors). Suite ran **81/81**, up from 62/62.

**Sprint 1 (earlier):**
- `GET /info/epics` endpoint exposing the 5 product backlog epics and their
  current status, so the dashboard and CI can surface sprint progress without
  reading the backlog file directly.
- `GET /info/sprint` endpoint returning the current sprint summary
  (`current_sprint`, `total_sprints`, `release`, `branch`).
- `docs/SPRINT_PLAN.md` mapping the product backlog (E1–E5) to a 5-sprint
  delivery roadmap.
- `CHANGELOG.md` at the project root (this file).
- `LICENSE` at the project root — proprietary / pre-commercial notice; will be
  replaced with a standard OSS or commercial license at v1.0.0.
- `Azure/README.md` explaining the three-way Azure layout (`Azure/` for
  planning prose, `.azure/` for live deployment status, `infra/bicep/` for IaC).

### Changed
- Registered the new `info` router in `enterprise_ai_backend/app/main.py`.
- `README.md` updated from "50/50 integration assertions" to the new count.
- `/info/epics` now reports Epic E2 as `in_progress` (Sprint 2 is active).
- `/info/sprint` now reports `current_sprint=2`.

### Removed
- Untracked four stale legacy draft folders from git (files remain on the
  author's disk, but are no longer part of the repository):
  - `Back in/` (old backend iterations, already in `.gitignore`)
  - `Front end/` (early draft text)
  - `Middle layer/` (early draft text)
  - `Enterprise readability AI Platform v1 Artificial Intelligence/` (misspelled
    legacy folder containing a duplicate NIST RMF PDF)
- `.gitignore` extended to prevent these legacy folders from being re-added.

## [0.3.0] - 2026-04-19

### Added
- Initial HR-ready release package of the Enterprise AI Reliability Platform.
- FastAPI backend with routers for `health`, `auth`, `reliability`,
  `assessments`, `ai`, and `hash`.
- React 18 + TypeScript + Vite frontend shell.
- Docker Compose dev stack.
- Azure Container Apps + Bicep infrastructure-as-code under `infra/`.
- GitHub Actions workflows: `ci-api`, `ci-web`, `ci-contracts`,
  `security-scans`, and `release`.
- Product backlog (`product_backlog/product_backlog.txt`) with 5 epics and
  15 stories.
- Documentation set under `docs/` including HR review guide, go/no-go
  checklist, and release evidence template.

### Security
- bcrypt password hashing and python-jose JWT issuance for auth.
- Baseline OWASP / dependency scanning via the `security-scans` workflow.

[Unreleased]: https://github.com/coconuthead-Sentinel-core/enterprise-ai-reliability-platform-v1/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/coconuthead-Sentinel-core/enterprise-ai-reliability-platform-v1/releases/tag/v0.3.0
