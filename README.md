# Enterprise AI Reliability Platform - v1 (EARP)

Production-grade platform for scoring and monitoring AI systems against the
NIST AI Risk Management Framework (GOVERN, MAP, MEASURE, MANAGE), with
reliability engineering math, policy gating, audit history, dashboard/reporting
surfaces, and local compliance evidence export.

**Status:** `v0.3.0`, full local build validated on 2026-04-21. Real FastAPI,
real bcrypt + JWT, real SQLite, real scikit-learn `IsolationForest`, and
378/378 integration assertions are passing on the current branch. Repo docs,
contracts, and release packaging are current on the branch. Azure credential
provisioning remains an external prerequisite intentionally excluded from the
current work cycle.

## Monorepo layout

```text
enterprise-ai-reliability-platform-v1/
|- api/                   Legacy signpost -> enterprise_ai_backend/
|- apps/
|  |- api/                 Signpost -> enterprise_ai_backend/
|  `- web/                 React 18 + TypeScript + Vite dashboard UI
|- enterprise_ai_backend/  FastAPI app, persistence, reporting, tests
|- libs/
|  |- schemas/             OpenAPI 3.1 contract exported from FastAPI
|  `- policy/              NIST AI RMF scoring policy
|- infra/
|  |- docker/              Local compose stack
|  `- bicep/               Azure Container Apps deployment
|- docs/                   Engineering and release docs
`- ...                     SDLC, architecture, risk, and compliance folders
```

The `enterprise_ai_backend/` folder is the only live API code tree. Both
`apps/api/` and `api/` are signpost folders kept for navigation and
backward-compatible repo wayfinding.

## Quickstart

### Backend

```bash
cd enterprise_ai_backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
python tests/test_backend.py
```

Key local endpoints:

- `/docs`
- `/policy/evaluate`
- `/policy/history`
- `/audit/history`
- `/audit/verify`
- `/compliance/retention/policy`
- `/compliance/retention/status`
- `/compliance/legal-holds`
- `/release/approvals/current`
- `/release/approvals/request`
- `/dashboard/summary`
- `/reports/executive-summary`
- `/reports/executive-summary.pdf`

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

The local web app opens at `http://127.0.0.1:5173` and expects the backend at
`http://127.0.0.1:8000`.

## Current product surface

- Reliability scoring with weighted composite output and NIST breakdown
- Policy evaluation with allow/warn/block decisions and hash-chained audit history
- Release approval workflow with separated Security Lead and Compliance Lead sign-off
- Retention policy and legal-hold controls for audited records
- Authenticated NIST AI RMF assessments with persisted gate outcomes
- Dashboard workspace with Release, Security, and Executive views
- JSON and PDF executive summary export
- Local compliance evidence bundle with control coverage, gaps, and next steps

## Validation snapshot

Validated locally on 2026-04-21:

- `python tests/test_backend.py`: pass, 378/378 assertions
- `python -m pytest -q`: pass, 2 tests
- `python -m pip check`: pass
- `python scripts/export_openapi.py`: pass
- `npm run typecheck`: pass
- `npm run build`: pass
- `npm audit --audit-level=moderate`: pass, 0 vulnerabilities
- `az bicep build --file infra/bicep/main.bicep`: pass

## CI/CD

GitHub Actions workflows:

1. `ci-api.yml`
2. `ci-web.yml`
3. `ci-contracts.yml`
4. `security-scans.yml`
5. `release.yml`

The release workflow always builds and pushes GHCR images. It only runs the
Azure deployment job when the selected environment exposes the required Azure
secrets; otherwise the Azure job is skipped and credential provisioning remains
an external follow-on task.

## Azure note

An Azure Pay-As-You-Go subscription is sufficient for this project. Credential
setup is external to the repo and intentionally excluded from the current work
cycle; live deployment can resume once those values are available.

## More docs

- `docs/README.md`
- `docs/SPRINT_PLAN.md`
- `docs/go-no-go.md`
- `docs/release-evidence.md`
