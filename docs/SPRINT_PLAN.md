# EARP Sprint Plan

Project: Enterprise AI Reliability Platform v1 (EARP)
Release target: v0.3.0
Owner: Shannon Bryan Kelly (`coconuthead-Sentinel-core`)
Working branch: `sprint-3/policy-audit-log`
As of: 2026-04-20

---

## Sprint status

| Sprint | Epic | Title | Status |
| --- | --- | --- | --- |
| 0 | baseline | Repo handoff and validation baseline | done |
| 1 | E1 | Evidence Ingestion and Normalization | shim delivered; backlog epic still open |
| 2 | E2 | Reliability Scoring Engine | done |
| 3 | E3 | Policy Gate Evaluation | done on the current branch head |
| 4 | E4 | Dashboard and Reporting | implemented locally; pending push/CI on the rolled-forward branch head |
| 5 | E5 | Security and Compliance | partial local implementation; cloud-only controls still blocked by Azure credentials |

PR #8 originally represented the exact Sprint 3 delivery branch. The same branch
now carries rolled-forward local Sprint 4 and Sprint 5 work.

The last Azure release-workflow attempt still ran against
`b29da3d9eaeedeae6ad64236c1a59b1961de1e8c`.

---

## Current routing

This project is being routed with an Eisenhower matrix plus the Cognitive Grid
so local product work, release evidence, and Azure blockers stay separated.

### Eisenhower matrix

| Bucket | Items |
| --- | --- |
| Do now | Finish local dashboard/reporting work, keep backend and frontend validation green, publish accurate release evidence for the rolled-forward branch head |
| Schedule next | Push the current branch head, rerun GitHub CI on the same head, decide whether to keep extending PR #8 or cut a new PR after review |
| Delegate / wait | Azure login, active Azure subscription access, GitHub `dev` environment secrets, Key Vault secret population, live FQDN discovery |
| Defer | Live smoke tests and public Azure URLs until Azure deployment credentials exist |

### Cognitive Grid

| Zone | Row family | Active items |
| --- | --- | --- |
| Green | Row 1 / immediate objective | Local Sprint 4 dashboard/reporting build, local Sprint 5 evidence bundle, clean validation |
| Green | Row 5 / active artifacts | `apps/web/src/App.tsx`, `apps/web/src/api.ts`, `enterprise_ai_backend/app/reporting.py`, `docs/SPRINT_PLAN.md`, `docs/go-no-go.md`, `docs/release-evidence.md` |
| Yellow | Row 2 / synthesis | Branch strategy after the rolled-forward local implementation, release evidence refresh |
| Red | Row 10 / archive evidence | CI run results, last Azure workflow result, validation command history, exact blocked secret list |
| Future | Row 13 / backlog horizon | Azure deploy, FQDN capture, live smoke tests, stronger approval separation, tamper-evident audit storage, retention/legal-hold automation |

---

## Delivered scope

### Sprint 3 delivered scope

Epic E3 is complete on the current branch head:

1. E3-S1: `POST /policy/evaluate`
   - Composite policy gate with `allow`, `warn`, and `block` outcomes.
   - Per-NIST floor enforcement and threshold override support.

2. E3-S2: policy gate attached to `/assessments`
   - Every assessment row persists `gate_decision` and `gate_reasons`.
   - The gate is computed from the same scores that produce `risk_tier`.

3. E3-S3: policy audit log
   - Every `/policy/evaluate` call is persisted.
   - `GET /policy/history` returns audit history plus trend stats.
   - SQLite compatibility migration upgrades older local databases that
     predate the new `assessments` gate columns.

### Sprint 4 local scope

Epic E4 is now implemented locally on the same branch:

1. `GET /dashboard/summary`
   - Role-aware dashboard payload with KPI cards, epic status, assessment
     posture, reliability score history, and policy history.

2. `GET /reports/executive-summary`
   - Structured executive summary combining the dashboard payload and the
     compliance evidence bundle.

3. `GET /reports/executive-summary.pdf`
   - ReportLab-generated PDF export for review and handoff workflows.

4. React dashboard workspace
   - Release, Security, and Executive views.
   - Local sample-data seeding flow.
   - PDF export button wired to the report endpoint.

### Sprint 5 local scope

Epic E5 now has a local evidence-bundle slice:

1. Compliance evidence bundle
   - Five controls covering auth, CI security scanning, audit traceability,
     release governance, and retention/legal-hold.

2. Outstanding gaps
   - Approval separation, immutable audit storage, retention/legal-hold
     automation, and Azure smoke-test completion remain open.

3. Recommended next steps
   - The report endpoints and dashboard now surface the exact local status and
     the remaining blockers.

---

## Validation snapshot

Validated locally on 2026-04-20:

- `python tests/test_backend.py`: pass, 313/313 assertions
- `python -m pytest -q`: pass, 2 tests
- `python -m pip check`: pass
- `python scripts/export_openapi.py`: pass
- `npm run typecheck`: pass
- `npm run build`: pass
- `npm audit --audit-level=moderate`: pass, 0 vulnerabilities
- `az bicep build --file infra/bicep/main.bicep`: pass

Validated on GitHub for the earlier PR #8 branch head:

- `ci-api`: green on Python 3.10, 3.11, 3.12
- `ci-contracts`: green
- `security-scans`: green

Release workflow evidence for `b29da3d`:

- `Build & push images`: success
- `Deploy to Azure Container Apps`: failed at `azure/login@v2`
  because Azure secrets are not configured in the GitHub `dev` environment

---

## Azure path

Azure is not blocked by subscription tier. An active Azure Pay-As-You-Go
subscription is sufficient for this project as long as it can create the
required resources and the account has permission to deploy them.

What is blocked right now:

- `az account show` on this laptop still requires `az login`
- GitHub repository secrets are empty
- GitHub `dev` environment secrets are empty
- no Azure service principal / federated credential values are available for:
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`
  - `AZURE_MANAGED_IDENTITY_ID`
  - `AZURE_KEY_VAULT_URI`

Once those values exist, the current release workflow is already far enough
along to:

1. build and push API and web images to GHCR,
2. run `azure/arm-deploy@v2` against `infra/bicep/main.bicep`,
3. surface the API and web FQDNs,
4. enable smoke tests against live URLs.

---

## Next execution slice

The next clean move is:

1. push the current rolled-forward branch head,
2. rerun GitHub CI against that exact head,
3. keep Azure deployment paused until credentials exist,
4. once secrets exist, rerun `release.yml`, collect the API and web FQDNs,
   and run smoke tests against the live URLs.
