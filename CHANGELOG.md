# Changelog

All notable changes to the Enterprise AI Reliability Platform (EARP) will be
documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

**Sprint 5 - Security and Compliance (Epic E5, local slice):**
- Added a repo-backed compliance evidence bundle with five control rows for
  auth boundaries, CI security scanning, audit traceability, release
  governance, and retention/legal hold.
- Added outstanding-gap and recommended-next-step reporting to the executive
  summary surface.
- Backend validation now passes 313/313 assertions.

**Sprint 4 - Dashboard and Reporting (Epic E4):**
- Added `GET /dashboard/summary` for role-aware dashboard metrics, epic
  progress, assessment posture, reliability score history, and policy history.
- Added `GET /reports/executive-summary` for a structured JSON executive
  summary.
- Added `GET /reports/executive-summary.pdf` for ReportLab-based PDF export.
- Added frontend dashboard views for Release, Security, and Executive
  workflows, plus local sample-data seeding and PDF export.
- Added backend reporting helpers that assemble dashboard payloads and render
  executive-summary PDFs.

**Sprint 3 - Policy Gate Evaluation (Epic E3, story E3-S3):**
- `POST /policy/evaluate` now persists each evaluation in a dedicated policy
  audit table.
- `GET /policy/history` returns the audit log plus trend stats, decision-rate
  summaries, rolling composite metrics, and decision transitions.
- SQLite compatibility migration support upgrades older local `assessments`
  tables that do not yet have `gate_decision` and `gate_reasons_json`.
- Added `test_sqlite_compat.py` to verify local upgrade behavior against a
  legacy SQLite database shape.

**Sprint 3 - Policy Gate Evaluation (Epic E3, story E3-S2):**
- `POST /assessments` now runs the policy gate against its own NIST-RMF
  scores and persists the decision alongside the assessment record, so
  `risk_tier` and the gate outcome never drift out of sync.
- `database.Assessment` extended with two nullable columns:
  - `gate_decision` (`allow` / `warn` / `block`)
  - `gate_reasons_json` (serialized `PolicyReason` list)
- `AssessmentOutput` schema extended with `gate_decision`
  (`Optional[PolicyDecision]`) and `gate_reasons: List[PolicyReason]`
  (default `[]`).

**Sprint 3 - Policy Gate Evaluation (Epic E3, story E3-S1):**
- `POST /policy/evaluate` runs a gate against a reliability score and returns
  an `allow` / `warn` / `block` decision with detailed reasons.
- Added policy schemas, threshold validation, and per-NIST floor enforcement.

**Sprint 2 - Reliability Scoring Engine (Epic E2, story E2-S3):**
- `GET /reliability/score/history` exposes persisted score history plus trend stats.
- Reliability score records are now persisted automatically by score endpoints.

**Sprint 2 - Reliability Scoring Engine (Epic E2, story E2-S2):**
- `POST /reliability/score/explain` adds structured explanation output for
  contributions, tier gaps, and weakest/strongest NIST functions.

**Sprint 2 - Reliability Scoring Engine (Epic E2, story E2-S1):**
- `POST /reliability/score` adds weighted composite reliability scoring
  across arbitrary components.

**Sprint 1 (earlier):**
- `GET /info/epics` exposes the 5 product backlog epics and their status.
- `GET /info/sprint` exposes the current sprint summary.
- Added `docs/SPRINT_PLAN.md`.
- Added `CHANGELOG.md`.
- Added `LICENSE`.
- Added `Azure/README.md`.

### Changed

- `enterprise_ai_backend/app/routers/info.py` now reports Sprint 3 as done and
  exposes Sprint 4 / Sprint 5 as active local work on the current branch head.
- `enterprise_ai_backend/scripts/export_openapi.py` now writes
  `libs/schemas/openapi.json` without the trailing newline that caused
  byte-for-byte drift in `ci-contracts`.
- `.github/workflows/release.yml` now lowercases GHCR repository paths before
  tagging images, which fixed image publishing for repositories with uppercase
  owner names.
- Release evidence, go/no-go, sprint, and Azure planning docs now reflect the
  rolled-forward local Sprint 4 / Sprint 5 work, the last Azure deployment
  attempt on `b29da3d`, and the current Azure credential blocker.
- Readmes and docs were refreshed to cover the dashboard/reporting endpoints,
  PDF export, and the current 313/313 validation result.

### Removed

- Untracked legacy draft folders remain excluded from git through `.gitignore`.

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
