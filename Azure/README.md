# Azure content — navigation map

Azure-related content lives in **three** places in this repo, on purpose.
This README exists so reviewers know which folder to open for which job.

| Folder | Purpose | Owner |
|--------|---------|-------|
| `Azure/` (this folder) | **Planning and deployment walkthroughs.** Prose docs explaining the intended Azure architecture, resource naming, and a human-readable deployment guide. | Shannon + Claude, editable |
| `.azure/` | **Live deployment status.** Machine- and CLI-adjacent notes, including `plan.md` which tracks what has actually been created in the subscription and which credentials are still missing. | Auto-updated during Azure work |
| `infra/bicep/` | **Infrastructure-as-code.** The Bicep templates that `release.yml` actually deploys (Container Apps env, Log Analytics, App Insights, Key Vault, user-assigned identity, API + Web apps). | CI/CD, code-reviewed |

## Quick picks

- **"What is the Azure design?"** → `Azure/Azure.txt`
- **"How do I deploy it by hand?"** → `Azure/DEPLOYMENT.md`
- **"What is actually live right now?"** → `.azure/plan.md`
- **"Show me the templates CI runs."** → `infra/bicep/main.bicep` and `infra/bicep/README.md`

## Status at a glance

As of `v0.3.0`, no resources have been created in Azure yet. Deployment is
blocked on four credential items that only Shannon can complete:

1. `gh auth login`
2. `az login`
3. GitHub Actions secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
   `AZURE_SUBSCRIPTION_ID`, `AZURE_MANAGED_IDENTITY_ID`, `AZURE_KEY_VAULT_URI`
4. Key Vault secrets: `jwt-secret`, `database-url`, `redis-url`

Once items 1–4 are done, tagging a release (`v*.*.*`) triggers
`.github/workflows/release.yml` which runs `azure/arm-deploy` against
`infra/bicep/main.bicep` into `rg-earp-<env>-centralus`.
