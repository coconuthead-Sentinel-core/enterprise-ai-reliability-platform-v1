# Azure Deployment Plan - Enterprise AI Reliability Platform v1

Status: Local validation complete; GitHub image publish verified; Azure deploy blocked on credentials

## 1. Summary

Deploy the EARP FastAPI API and React/Vite web client to Azure Container Apps in `centralus`.

## 2. Recipe

- Type: Bicep with GitHub Actions release workflow
- Infrastructure root: `infra/bicep`
- Release workflow: `.github/workflows/release.yml`
- Container registry: GitHub Container Registry (`ghcr.io`)

## 3. Azure resources

| Resource | Naming pattern |
| --- | --- |
| Resource group | `rg-earp-dev-centralus` |
| Log Analytics | `law-earp-dev-centralus` |
| Application Insights | `ai-earp-dev-centralus` |
| Container Apps environment | `cae-earp-dev-centralus` |
| API app | `ca-earp-api-dev-centralus` |
| Web app | `ca-earp-web-dev-centralus` |
| Key Vault | `kv-earp-dev-centralus` |
| User-assigned identity | `uami-earp-dev-centralus` |

## 4. Secrets and identity

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

## 5. Application components

- API: `enterprise_ai_backend/Dockerfile`, port `8000`, health probe `/health`
- Web: `apps/web/Dockerfile`, port `80`, runtime API configuration through `API_BASE_URL`
- Contracts: `libs/schemas/openapi.json`

## 6. Validation plan

Run before deployment:

- `python tests/test_backend.py` from `enterprise_ai_backend`
- `python -m pytest -q` from `enterprise_ai_backend`
- `python -m pip check` from `enterprise_ai_backend`
- `python scripts/export_openapi.py` from `enterprise_ai_backend`
- `npm install`, `npm run typecheck`, `npm audit --audit-level=moderate`, and `npm run build` from `apps/web`
- `az bicep build --file infra/bicep/main.bicep`

## 7. Validation proof

Completed locally on 2026-04-20:

- Backend integration: `.\.venv\Scripts\python.exe tests\test_backend.py` passed with 286/286 assertions.
- Backend pytest: `.\.venv\Scripts\python.exe -m pytest -q` passed with 2 tests.
- Backend dependencies: `.\.venv\Scripts\python.exe -m pip check` reported no broken requirements.
- Contract export: `.\.venv\Scripts\python.exe scripts\export_openapi.py` regenerated `libs/schemas/openapi.json`.
- Frontend build path: `npm install`, `npm run typecheck`, `npm audit --audit-level=moderate`, and `npm run build` passed.
- Bicep syntax: `az bicep build --file infra/bicep/main.bicep` passed.

Completed on GitHub for the current PR #8 branch head:

- PR CI checks are green.
- Release workflow run `24663922506` successfully built and pushed API and web images to GHCR from `b29da3d9eaeedeae6ad64236c1a59b1961de1e8c`.

Blocked:

- `az account show` on the laptop still requires `az login`.
- `azure/login@v2` in GitHub Actions fails because the `dev` environment secrets are not configured.

## 8. Subscription note

Azure Pay-As-You-Go is sufficient for this project. No enterprise subscription is required.
The blocker is access to an active subscription plus the credential values above.

## 9. Deployment command

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
