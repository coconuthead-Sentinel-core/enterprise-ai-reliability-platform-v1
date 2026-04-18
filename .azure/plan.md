# Azure Deployment Plan - Enterprise AI Reliability Platform v1

Status: Locally Validated; Cloud Deployment Blocked On Authentication

## 1. Summary

Deploy the EARP FastAPI API and React/Vite web client to Azure Container Apps in `centralus`.

## 2. Recipe

- Type: Bicep with GitHub Actions release workflow
- Infrastructure root: `infra/bicep`
- Release workflow: `.github/workflows/release.yml`
- Container registry: GitHub Container Registry (`ghcr.io`)

## 3. Azure Resources

| Resource | Naming Pattern |
| --- | --- |
| Resource group | `rg-earp-dev-centralus` |
| Log Analytics | `law-earp-dev-centralus` |
| Application Insights | `ai-earp-dev-centralus` |
| Container Apps environment | `cae-earp-dev-centralus` |
| API app | `ca-earp-api-dev-centralus` |
| Web app | `ca-earp-web-dev-centralus` |
| Key Vault | `kv-earp-dev-centralus` |
| User-assigned identity | `uami-earp-dev-centralus` |

## 4. Secrets And Identity

GitHub environment secrets required:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_MANAGED_IDENTITY_ID`
- `AZURE_KEY_VAULT_URI`

Key Vault secrets required:

- `jwt-secret`
- `database-url`
- `redis-url`

## 5. Application Components

- API: `enterprise_ai_backend/Dockerfile`, port `8000`, health probe `/health`
- Web: `apps/web/Dockerfile`, port `80`, runtime API configuration through `API_BASE_URL`
- Contracts: `libs/schemas/openapi.json`

## 6. Validation Plan

Run before deployment:

- `python test_backend.py` from `enterprise_ai_backend`
- `python scripts/export_openapi.py` from `enterprise_ai_backend`
- `npm install`, `npm run typecheck`, and `npm run build` from `apps/web`
- `az bicep build --file infra/bicep/main.bicep`

## 7. Validation Proof

Completed locally on 2026-04-18:

- Backend integration: `.\.venv\Scripts\python.exe test_backend.py` passed with 50/50 real assertions.
- Backend pytest: `.\.venv\Scripts\python.exe -m pytest -q` passed with 1 collected integration test.
- Backend dependencies: `.\.venv\Scripts\python.exe -m pip check` reported no broken requirements.
- Contract export: `.\.venv\Scripts\python.exe scripts\export_openapi.py` regenerated `libs/schemas/openapi.json`.
- Frontend install/build: `npm install`, `npm run typecheck`, `npm audit --audit-level=moderate`, and `npm run build` passed.
- Bicep syntax: `az bicep build --file infra/bicep/main.bicep` passed.

Cloud deployment is blocked until `gh auth login` and `az login` are completed by the user.

## 8. Deployment Command

Deployment is executed by `.github/workflows/release.yml` after GitHub secrets and Azure prerequisites are configured. Manual deployment may use:

```powershell
az deployment group create `
  --resource-group rg-earp-dev-centralus `
  --file infra/bicep/main.bicep `
  --parameters env=dev `
  --parameters region=centralus `
  --parameters registryRepo=$env:GITHUB_REPOSITORY `
  --parameters managedIdentityId=$env:AZURE_MANAGED_IDENTITY_ID `
  --parameters keyVaultUri=$env:AZURE_KEY_VAULT_URI
```
