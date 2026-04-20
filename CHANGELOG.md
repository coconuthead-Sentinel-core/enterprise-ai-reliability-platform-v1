# Changelog

All notable changes to the Enterprise AI Reliability Platform (EARP) will be
documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
