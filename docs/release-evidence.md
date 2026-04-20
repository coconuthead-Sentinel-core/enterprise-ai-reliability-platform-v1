# Release Evidence

Date: 2026-04-20

## Environment Findings

- `git` is installed.
- Node.js LTS, GitHub CLI, and Azure CLI were installed during release preparation.
- `gh auth status` succeeds for `coconuthead-Sentinel-core`; the public repo exists and PR workflows are queryable from this laptop.
- `az account show` reports `az login` is required; Azure resource creation and deployment are blocked until login.
- Backend dependencies are installed in `enterprise_ai_backend/.venv`.
- Frontend dependencies are installed in `apps/web/node_modules`; generated artifacts remain ignored.
- `git fetch origin --prune` confirms local `HEAD` is `2a0b8b3`, `origin/main` is `fdff55e`, and the laptop branch is 2 commits ahead of `main`.

## Validation Evidence

| Evidence | Command | Status |
| --- | --- | --- |
| Backend install | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` | Pass |
| Backend tests | `.\.venv\Scripts\python.exe tests\test_backend.py` | Pass: 286/286 real assertions |
| Backend pytest | `.\.venv\Scripts\python.exe -m pytest -q` | Pass: 2 tests, 2 FastAPI deprecation warnings |
| Backend dependency check | `.\.venv\Scripts\python.exe -m pip check` | Pass |
| OpenAPI export | `.\.venv\Scripts\python.exe scripts\export_openapi.py` | Pass: refreshed contract includes `GET /policy/history` |
| Frontend install | `npm install` | Pass |
| Frontend typecheck | `npm run typecheck` | Pass |
| Frontend audit | `npm audit --audit-level=moderate` | Pass: 0 vulnerabilities |
| Frontend build | `npm run build` | Pass |
| Bicep validation | `az bicep build --file infra/bicep/main.bicep` | Pass |
| GitHub publish | `gh auth status`, `gh pr list`, `gh run list` | Partial: public repo exists, PR #7 is open, and the latest runs for `2a0b8b3` succeeded; unpublished E3-S3 laptop changes remain local |
| Azure deploy | `az deployment group create ...` | Blocked: Azure CLI not authenticated |

## Live URLs

- Web URL: pending Azure deployment.
- API URL: pending Azure deployment.

## Release Recommendation

Current recommendation: `no-go` for public HR review until the unpublished laptop delta is pushed, CI is green on that exact delta, Azure deployment succeeds, and live smoke tests populate the URLs above.
