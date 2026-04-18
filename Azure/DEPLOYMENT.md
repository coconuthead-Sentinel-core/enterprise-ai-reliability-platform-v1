# Azure deployment supplement

`Azure.txt` (in this folder) is the canonical readiness guide. This
file is the short, code-pointer version: it maps every claim in
`Azure.txt` to the exact file in the repo that implements it.

## Infrastructure-as-code

| Azure.txt section | Implemented in |
|-------------------|----------------|
| Resource group + naming (`rg-earp-<env>-<region>`) | `infra/bicep/main.bicep` |
| Container Apps Environment | `infra/bicep/main.bicep` (`Microsoft.App/managedEnvironments`) |
| API Container App (`ca-earp-api-<env>-<region>`) | `infra/bicep/main.bicep` |
| Web Container App (`ca-earp-web-<env>-<region>`) | `infra/bicep/main.bicep` |
| Azure Container Registry / GHCR | Images pushed to `ghcr.io/<owner>/<repo>/api` and `.../web` by `.github/workflows/release.yml` |
| Key Vault secrets (`jwt-secret`, `database-url`, `redis-url`) | `infra/bicep/main.bicep` wires them as `secretRef` to the API container |
| Managed identity (user-assigned) + Key Vault Secrets User role | `infra/bicep/main.bicep` |
| Log Analytics + Application Insights | `infra/bicep/main.bicep` |
| Dev parameter file | `infra/bicep/main.parameters.dev.json` |

## CI/CD

| Azure.txt requirement | Implemented in |
|-----------------------|----------------|
| GitHub OIDC federated credential to Azure AD | `AZURE_CLIENT_ID` secret consumed by `.github/workflows/release.yml` |
| Build and push container images on tag | `.github/workflows/release.yml` (step `build-and-push`) |
| ARM / Bicep deploy | `.github/workflows/release.yml` (step `deploy-bicep`) |
| Python 3.10 / 3.11 / 3.12 matrix | `.github/workflows/ci-api.yml` |
| Web typecheck + build | `.github/workflows/ci-web.yml` |
| OpenAPI drift detection | `.github/workflows/ci-contracts.yml` |
| Security scans (pip-audit, npm audit, gitleaks, CodeQL) | `.github/workflows/security-scans.yml` |

## Required GitHub environment secrets

| Secret | Purpose |
|--------|---------|
| `AZURE_SUBSCRIPTION_ID` | Target subscription for the deploy |
| `AZURE_TENANT_ID` | Tenant for OIDC login |
| `AZURE_CLIENT_ID` | App registration with federated credential for the GitHub repo |

## Release + rollback

The release flow (bump version → tag → CI pushes images → Bicep
deploy) is documented in `RELEASE.md` at the repo root. Rollback
commands (revision list + revision activate) are in the same file.

## Runbooks

Operational runbooks, on-call escalation, and incident templates
live in `incident_response_runbook/` at the repo root. They are
referenced from `SECURITY.md` and from the rollback section of
`RELEASE.md`.
