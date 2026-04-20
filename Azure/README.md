# Azure content - navigation map

Azure-related content lives in three places in this repo, on purpose.
This README exists so reviewers know which folder to open for which job.

| Folder | Purpose | Owner |
| --- | --- | --- |
| `Azure/` | Planning and deployment walkthroughs. Human-readable Azure design and manual deployment guidance. | Shannon + collaborators |
| `.azure/` | Live deployment status and current credential blockers. | Updated during Azure work |
| `infra/bicep/` | Infrastructure as code used by CI/CD. | Code-reviewed source of truth |

## Quick picks

- Azure design: `Azure/Azure.txt`
- Manual deployment guide: `Azure/DEPLOYMENT.md`
- Current live status: `.azure/plan.md`
- Templates used by CI: `infra/bicep/main.bicep` and `infra/bicep/README.md`

## Status at a glance

As of 2026-04-20:

- no Azure resources have been created yet,
- PR #8 head `933f86a` is green on GitHub CI,
- release workflow run `24663922506` successfully built and pushed images,
- Azure deployment is blocked at `azure/login@v2` because the required GitHub
  `dev` environment secrets are not configured.

## What is still needed

1. Access to an active Azure subscription
2. Azure identity values for:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
   - `AZURE_MANAGED_IDENTITY_ID`
   - `AZURE_KEY_VAULT_URI`
3. Key Vault secrets:
   - `jwt-secret`
   - `database-url`
   - `redis-url`

An enterprise Azure subscription is not required. Azure Pay-As-You-Go is sufficient
for this deployment path once the account has billing enabled and permission to
create the required resources.
