# Release process

## Versioning

Semantic versioning: `MAJOR.MINOR.PATCH`.

* **MAJOR** — breaking API contract change (`libs/schemas/openapi.json`
  deletes or changes the type of a field)
* **MINOR** — new endpoint, new feature, new column
* **PATCH** — bug fix, doc fix, dependency bump

## Release steps

### 1. Open a release branch

```bash
git checkout develop
git pull
git checkout -b release/v0.4.0
```

### 2. Update version

Bump `APP_VERSION` in:

* `enterprise_ai_backend/.env.example`
* `enterprise_ai_backend/.env`
* `apps/web/package.json`
* `enterprise_ai_backend/app/config.py` default

### 3. Regenerate the API contract

```bash
cd enterprise_ai_backend
python -c "import json; from app.main import app; \
  open('../libs/schemas/openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
```

### 4. Update CHANGELOG

Add a section to `CHANGELOG.md` with:

* Added
* Changed
* Deprecated
* Removed
* Fixed
* Security

### 5. Open a PR into `main`

* Require CODEOWNERS approval
* All 5 CI workflows green

### 6. Tag

```bash
git checkout main
git pull
git tag v0.4.0
git push origin v0.4.0
```

The `release.yml` workflow will:

1. Build and push `ghcr.io/<owner>/.../api:v0.4.0` + `web:v0.4.0`
2. Run `az login` via OIDC
3. Deploy `infra/bicep/main.bicep` to `rg-earp-<env>-eastus`
4. New revision is rolled out by Container Apps

### 7. Smoke-test prod

```bash
curl https://ca-earp-api-prod-eastus.azurecontainerapps.io/health
curl https://ca-earp-api-prod-eastus.azurecontainerapps.io/
```

Both must return 200 with the new `app_version`.

### 8. Back-merge to `develop`

```bash
git checkout develop
git merge main
git push
```

## Rollback

1. `az containerapp revision list -n ca-earp-api-prod-eastus -g rg-earp-prod-eastus`
2. `az containerapp revision activate -n ca-earp-api-prod-eastus -g rg-earp-prod-eastus --revision <previous-revision>`
3. File an incident per `incident_response_runbook/`.

## Required GitHub environment secrets

Per `Azure/Azure.txt`, the `release.yml` workflow needs:

* `AZURE_SUBSCRIPTION_ID`
* `AZURE_TENANT_ID`
* `AZURE_CLIENT_ID` (federated credential for GitHub OIDC)
