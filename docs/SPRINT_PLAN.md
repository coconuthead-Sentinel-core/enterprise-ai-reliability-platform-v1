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
| 3 | E3 | Policy Gate Evaluation | implemented on PR #8 |
| 4 | E4 | Dashboard and Reporting | queued next |
| 5 | E5 | Security and Compliance | planned |

PR #8 (`sprint-3/policy-audit-log` -> `main`) is the exact Sprint 3 delivery branch.
Its head commit is `b29da3d9eaeedeae6ad64236c1a59b1961de1e8c`.

---

## Current routing

This project is now being routed with an Eisenhower matrix plus the Cognitive Grid
so urgent release blockers do not compete with future sprint work.

### Eisenhower matrix

| Bucket | Items |
| --- | --- |
| Do now | Keep PR #8 evidence accurate, preserve green CI on `b29da3d`, remove stale temp artifacts, document the real Azure blocker |
| Schedule next | Start Sprint 4 dashboard/reporting work on a fresh branch after Sprint 3 is merged or intentionally rolled forward |
| Delegate / wait | Azure login, active Azure subscription access, GitHub `dev` environment secrets, Key Vault secret population |
| Defer | Live smoke tests and public Azure URLs until Azure deployment credentials exist |

### Cognitive Grid

| Zone | Row family | Active items |
| --- | --- | --- |
| Green | Row 1 / immediate objective | Sprint 3 release-readiness truth, PR #8 status, CI evidence |
| Green | Row 5 / active artifacts | `docs/SPRINT_PLAN.md`, `docs/go-no-go.md`, `docs/release-evidence.md`, `.azure/plan.md`, `Azure/README.md` |
| Yellow | Row 2 / synthesis | Sprint 4 scope slicing and branch handoff notes |
| Red | Row 10 / archive evidence | CI run results, release workflow evidence, exact commit hash, local validation commands |
| Future | Row 13 / backlog horizon | Azure live deploy, smoke tests, Sprint 4 branch, Sprint 5 compliance bundle |

---

## Sprint 3 delivered scope

Epic E3 is implemented on PR #8 in three stories:

1. E3-S1: `POST /policy/evaluate`
   - Composite policy gate with `allow`, `warn`, and `block` outcomes.
   - Per-NIST floor enforcement and threshold override support.

2. E3-S2: policy gate attached to `/assessments`
   - Every assessment row now persists `gate_decision` and `gate_reasons`.
   - The gate is computed from the same scores that produce `risk_tier`.

3. E3-S3: policy audit log
   - Every `/policy/evaluate` call is persisted.
   - `GET /policy/history` returns audit history plus trend stats.
   - SQLite compatibility migration upgrades older local databases that
     predate the new `assessments` gate columns.

Sprint 3 release hardening also landed on the same branch:

- `enterprise_ai_backend/scripts/export_openapi.py` now writes
  `libs/schemas/openapi.json` in the byte shape expected by `ci-contracts`.
- `.github/workflows/release.yml` now lowercases GHCR repository paths, which
  allowed the image build/push job to succeed on `b29da3d`.

---

## Validation snapshot

Validated locally on 2026-04-20:

- `python tests/test_backend.py`: pass, 286/286 assertions
- `python -m pytest -q`: pass, 2 tests
- `python -m pip check`: pass
- `python scripts/export_openapi.py`: pass
- `npm run typecheck`: pass
- `npm run build`: pass
- `npm audit --audit-level=moderate`: pass, 0 vulnerabilities
- `az bicep build --file infra/bicep/main.bicep`: pass

Validated on GitHub for PR #8 head `b29da3d`:

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
required resources and the account has billing and permission to deploy them.

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

The next clean sprint move is:

1. merge or intentionally roll forward PR #8,
2. branch for Sprint 4 dashboard/reporting,
3. build the operator dashboard on top of the now-stable E2 and E3 endpoints,
4. return to Azure deployment only when credentials and subscription access exist.
