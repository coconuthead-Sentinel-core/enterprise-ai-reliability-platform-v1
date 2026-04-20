# Go/No-Go Checklist

Candidate: Enterprise AI Reliability Platform v1 (`v0.3.0`)

## Gate Status

| Gate | Status | Evidence |
| --- | --- | --- |
| Source repository initialized | Pass | Public GitHub repo exists at `coconuthead-Sentinel-core/enterprise-ai-reliability-platform-v1`; `origin/main` resolves to `fdff55e`. |
| Backend dependencies installed | Pass | Backend `.venv` installed from `enterprise_ai_backend/requirements.txt`. |
| Backend integration tests | Pass | `.\.venv\Scripts\python.exe tests\test_backend.py` passed 286/286 assertions on 2026-04-20. |
| Backend pytest | Pass | `.\.venv\Scripts\python.exe -m pytest -q` passed 2 tests on 2026-04-20. |
| Frontend dependencies installed | Pass | `npm install` completed and generated `apps/web/package-lock.json`. |
| Frontend typecheck/build | Pass | `npm run typecheck` and `npm run build` passed. |
| Dependency audit | Pass | `pip check` passed; `npm audit --audit-level=moderate` found 0 vulnerabilities after Vite upgrade. |
| API contract export | Pass | `.\.venv\Scripts\python.exe scripts\export_openapi.py` regenerated `libs/schemas/openapi.json`, including `GET /policy/history`. |
| Public repo safe to publish | Pass | `.env`, DB files, caches, virtualenvs, `node_modules`, build artifacts, local archives, and staging folders are ignored. |
| Bicep validation | Pass | `az bicep build --file infra/bicep/main.bicep` passed. |
| Azure deployment | Blocked | Azure CLI is installed, but `az account show` reports that `az login` is required. |
| GitHub publish | Partial | `gh auth status` is healthy, PR #7 is open, and the latest `sprint-3/policy-gate-assessments` CI runs for `2a0b8b3` are green. The laptop branch is still 2 commits ahead of `origin/main` and also has unpublished E3-S3 work. |

## Release Decision

Current decision: `no-go` for public release until the current laptop delta is published with green CI, Azure login succeeds, and live smoke testing is completed.

## Required Before Go

- Azure Container Apps deployment returns a working web URL and API `/health` URL.
- The current local branch delta is pushed and CI is green on that exact commit.
