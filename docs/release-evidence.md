# Release Evidence

Date: 2026-04-20
Candidate branch: `sprint-3/policy-audit-log`
Candidate commit: `b29da3d9eaeedeae6ad64236c1a59b1961de1e8c`
Candidate PR: `#8`

## Environment findings

- `git` is installed and the local repo tracks GitHub successfully.
- GitHub CLI authentication is healthy for `coconuthead-Sentinel-core`.
- Azure CLI is installed, but `az account show` still reports that `az login`
  is required on this laptop.
- Backend dependencies are installed in `enterprise_ai_backend/.venv`.
- Frontend dependencies are installed in `apps/web/node_modules`.
- GitHub repository secrets are empty.
- GitHub `dev` environment secrets are empty.

## Validation evidence

| Evidence | Command | Status |
| --- | --- | --- |
| Backend install | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` | Pass |
| Backend tests | `.\.venv\Scripts\python.exe tests\test_backend.py` | Pass: 286/286 assertions |
| Backend pytest | `.\.venv\Scripts\python.exe -m pytest -q` | Pass: 2 tests, 2 FastAPI deprecation warnings |
| Backend dependency check | `.\.venv\Scripts\python.exe -m pip check` | Pass |
| OpenAPI export | `.\.venv\Scripts\python.exe scripts\export_openapi.py` | Pass |
| Frontend install | `npm install` | Pass |
| Frontend typecheck | `npm run typecheck` | Pass |
| Frontend build | `npm run build` | Pass |
| Frontend audit | `npm audit --audit-level=moderate` | Pass: 0 vulnerabilities |
| Bicep validation | `az bicep build --file infra/bicep/main.bicep` | Pass |

## GitHub evidence

PR #8 head commit `b29da3d`:

- `ci-api`: success on Python 3.10, 3.11, and 3.12
- `ci-contracts`: success
- `security-scans`: success

Release workflow `24663922506` on the same commit:

- `Build & push images`: success
- `Deploy to Azure Container Apps`: failed at `azure/login@v2`
- `Deploy Bicep`: not reached because Azure login failed first

## Azure evidence

The current blocker is credentials, not subscription tier:

- no Azure login is active on this laptop,
- no GitHub Azure secrets are configured,
- no live Azure FQDNs exist yet.

An active Azure Pay-As-You-Go subscription is sufficient for this project once
it is attached to the account used for deployment and the required secret values
are available.

## Live URLs

- Web URL: pending Azure deployment
- API URL: pending Azure deployment

## Release recommendation

Current recommendation: `no-go` for a live public release until Azure
deployment completes and smoke tests confirm the live API and web URLs.
