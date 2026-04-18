# Release Evidence

Date: 2026-04-18

## Environment Findings

- `git` is installed.
- Node.js LTS, GitHub CLI, and Azure CLI were installed during release preparation.
- `gh auth status` reports no authenticated GitHub host; public repository creation and push are blocked until `gh auth login`.
- `az account show` reports `az login` is required; Azure resource creation and deployment are blocked until login.
- Backend dependencies are installed in `enterprise_ai_backend/.venv`.
- Frontend dependencies are installed in `apps/web/node_modules`; generated artifacts remain ignored.

## Validation Evidence

| Evidence | Command | Status |
| --- | --- | --- |
| Backend install | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` | Pass |
| Backend tests | `.\.venv\Scripts\python.exe test_backend.py` | Pass: 50/50 real assertions |
| Backend pytest | `.\.venv\Scripts\python.exe -m pytest -q` | Pass: 1 test, 2 FastAPI deprecation warnings |
| Backend dependency check | `.\.venv\Scripts\python.exe -m pip check` | Pass |
| OpenAPI export | `.\.venv\Scripts\python.exe scripts\export_openapi.py` | Pass |
| Frontend install | `npm install` | Pass |
| Frontend typecheck | `npm run typecheck` | Pass |
| Frontend audit | `npm audit --audit-level=moderate` | Pass: 0 vulnerabilities |
| Frontend build | `npm run build` | Pass |
| Bicep validation | `az bicep build --file infra/bicep/main.bicep` | Pass |
| GitHub publish | `gh repo create ...` and `git push` | Blocked: GitHub CLI not authenticated |
| Azure deploy | `az deployment group create ...` | Blocked: Azure CLI not authenticated |

## Live URLs

- Web URL: pending Azure deployment.
- API URL: pending Azure deployment.

## Release Recommendation

Current recommendation: `no-go` for public HR review until the repository is pushed, CI is green, Azure deployment succeeds, and live smoke tests populate the URLs above.
