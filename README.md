# Enterprise AI Reliability Platform - v1 (EARP)

Production-grade platform for scoring and monitoring AI systems against the
NIST AI Risk Management Framework (GOVERN, MAP, MEASURE, MANAGE), with
reliability engineering math, policy gating, audit history, dashboard/reporting
surfaces, and local compliance evidence export.

**Status:** `v0.3.0`, full local build validated. Real FastAPI, real bcrypt +
JWT, real SQLite, real scikit-learn `IsolationForest`, and 378/378 integration
assertions passing on the current laptop branch.

## Monorepo layout

```text
enterprise-ai-reliability-platform-v1/
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

Validated locally on 2026-04-20:

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

The last Azure release attempt built and pushed both images successfully, then
stopped at `azure/login@v2` because the GitHub `dev` environment does not yet
have the required Azure secrets.

## Azure note

An Azure Pay-As-You-Go subscription is sufficient for this project. The current
deployment blocker is credential setup, not subscription tier.

## More docs

- `docs/README.md`
- `docs/SPRINT_PLAN.md`
- `docs/go-no-go.md`
- `docs/release-evidence.md`
