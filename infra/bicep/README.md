# Azure Container Apps Deployment

This Bicep template deploys the EARP API and web containers to Azure Container Apps in `Central US` by default.

## One-time Azure prerequisites

Create the resource group, user-assigned managed identity, Key Vault, and required secrets before running the deployment. Set the secret values in your shell first, then write them into Key Vault:

```powershell
az group create -n rg-earp-dev-centralus -l centralus
az identity create -n uami-earp-dev-centralus -g rg-earp-dev-centralus -l centralus
az keyvault create -n kv-earp-dev-centralus -g rg-earp-dev-centralus -l centralus --enable-rbac-authorization true
az keyvault secret set --vault-name kv-earp-dev-centralus --name jwt-secret --value $env:EARP_JWT_SECRET
az keyvault secret set --vault-name kv-earp-dev-centralus --name database-url --value $env:EARP_DATABASE_URL
az keyvault secret set --vault-name kv-earp-dev-centralus --name redis-url --value $env:EARP_REDIS_URL
```

Grant the managed identity permission to read Key Vault secrets before deploying.

## Deploy manually

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

## GitHub Actions deployment

The `release.yml` workflow builds API and web images, pushes them to GHCR, and passes `${{ github.repository }}` into Bicep as `registryRepo`.

Required GitHub environment secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_MANAGED_IDENTITY_ID`
- `AZURE_KEY_VAULT_URI`

## Runtime web configuration

The web image writes `/config.js` at container startup from `API_BASE_URL`. This is required because Vite environment variables are normally baked into static assets at build time.
