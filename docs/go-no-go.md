# Go/No-Go Checklist

Candidate: Enterprise AI Reliability Platform v1 (`v0.3.0`)

## Gate Status

| Gate | Status | Evidence |
| --- | --- | --- |
| Source repository initialized | Pass | Local Git repo initialized on `main`. |
| Backend dependencies installed | Pass | Backend `.venv` installed from `enterprise_ai_backend/requirements.txt`. |
| Backend integration tests | Pass | `.\.venv\Scripts\python.exe test_backend.py` passed 50/50 assertions. |
| Backend pytest | Pass | `.\.venv\Scripts\python.exe -m pytest -q` passed 1 integration test. |
| Frontend dependencies installed | Pass | `npm install` completed and generated `apps/web/package-lock.json`. |
| Frontend typecheck/build | Pass | `npm run typecheck` and `npm run build` passed. |
| Dependency audit | Pass | `pip check` passed; `npm audit --audit-level=moderate` found 0 vulnerabilities after Vite upgrade. |
| API contract export | Pass | `.\.venv\Scripts\python.exe scripts\export_openapi.py` regenerated `libs/schemas/openapi.json`. |
| Public repo safe to publish | Pass | `.env`, DB files, caches, virtualenvs, `node_modules`, build artifacts, local archives, and staging folders are ignored. |
| Bicep validation | Pass | `az bicep build --file infra/bicep/main.bicep` passed. |
| Azure deployment | Blocked | Azure CLI is installed, but `az account show` reports that `az login` is required. |
| GitHub push | Blocked | GitHub CLI is installed, but `gh auth status` reports no authenticated GitHub host. |

## Release Decision

Current decision: `no-go` for public release until GitHub authentication, public push, Azure login, and live smoke testing are completed.

## Required Before Go

- Azure Container Apps deployment returns a working web URL and API `/health` URL.
- GitHub repository is created publicly and CI is green on the pushed commit.
