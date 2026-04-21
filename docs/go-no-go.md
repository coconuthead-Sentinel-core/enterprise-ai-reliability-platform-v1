# Go/No-Go Checklist

Candidate: Enterprise AI Reliability Platform v1 (`v0.3.0`)
Review date: 2026-04-21

## Gate status

| Gate | Status | Evidence |
| --- | --- | --- |
| Source repository initialized | Pass | Public GitHub repo exists at `coconuthead-Sentinel-core/enterprise-ai-reliability-platform-v1`; PR #8 is open from `sprint-3/policy-audit-log` into `main`. |
| Backend dependencies installed | Pass | Backend virtualenv is installed from `enterprise_ai_backend/requirements.txt`. |
| Backend integration tests | Pass | `.\.venv\Scripts\python.exe tests\test_backend.py` passed 378/378 assertions on 2026-04-21. |
| Backend pytest | Pass | `.\.venv\Scripts\python.exe -m pytest -q` passed 2 tests on 2026-04-21. |
| Frontend dependencies installed | Pass | `npm install` completed for `apps/web`. |
| Frontend typecheck/build | Pass | `npm run typecheck` and `npm run build` passed on 2026-04-21. |
| Dependency audit | Pass | `pip check` passed; `npm audit --audit-level=moderate` found 0 vulnerabilities. |
| API contract export | Pass | `.\.venv\Scripts\python.exe scripts\export_openapi.py` regenerated `libs/schemas/openapi.json`, including the audit, compliance, dashboard, and executive-report endpoints, in the byte shape expected by CI. |
| Public repo safe to publish | Pass | Ignore rules cover secrets, virtualenvs, node modules, caches, build outputs, local archives, and staging folders. |
| Bicep validation | Pass | `az bicep build --file infra/bicep/main.bicep` passed. |
| GitHub CI on exact current Sprint 3 branch head | Pass | PR #8 checks are green on the current branch head for `ci-api`, `ci-contracts`, and `security-scans`. |
| Release image publish | Pass | GitHub Actions run `24663922506` built and pushed API and web images successfully after the GHCR lowercase fix. |
| Release workflow without Azure credentials | Pass | `.github/workflows/release.yml` now publishes GHCR images and skips the Azure deployment job when the required Azure secrets are absent in the selected environment. |
| Azure deployment | Excluded | Live Azure deployment is intentionally outside the current work cycle because credential provisioning is external to the repo. |

## Release decision

Current repo-completion decision: `go`

Current live-release decision: `no-go`

Reason:

- code, docs, tests, contracts, and GHCR packaging are current on the branch,
- Azure credential provisioning is intentionally excluded from this work cycle,
- therefore no live API or web URLs exist yet, and public Azure release remains deferred.

## Required before live Azure go

- Add the GitHub `dev` environment secrets:
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`
  - `AZURE_MANAGED_IDENTITY_ID`
  - `AZURE_KEY_VAULT_URI`
- Ensure the Azure account used for deployment has an active subscription and
  permission to create the required resources.
- Re-run `release.yml` against the current PR #8 branch head after Azure secrets are configured.
- Capture the resulting API and web FQDNs.
- Run live smoke tests against those URLs.

An enterprise subscription is not required. An active Azure Pay-As-You-Go
subscription is sufficient for this deployment path.
