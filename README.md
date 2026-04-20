# Enterprise AI Reliability Platform — v1 (EARP)

Production-grade platform for scoring and monitoring AI systems against
the NIST AI Risk Management Framework (GOVERN, MAP, MEASURE, MANAGE),
with reliability engineering math (MTBF/MTTR/availability/reliability)
and real ML-based anomaly detection.

**Status:** v0.3.0, full build online. Real FastAPI, real bcrypt + JWT,
real scikit-learn IsolationForest, real SQLite in dev /
PostgreSQL-ready in prod. 116/116 integration assertions pass.

## Monorepo layout

```
enterprise-ai-reliability-platform-v1/
├─ apps/
│  ├─ api/               Signpost → enterprise_ai_backend/ (live FastAPI)
│  └─ web/               React 18 + TypeScript + Vite frontend
│
├─ enterprise_ai_backend/   The actual backend source tree
│  ├─ app/                  FastAPI app (auth, assessments, ai, reliability)
│  ├─ tests/                Integration test suite (116 assertions)
│  └─ requirements.txt
│
├─ libs/
│  ├─ schemas/            OpenAPI 3.1 contract (exported from FastAPI)
│  └─ policy/             NIST AI RMF scoring policy (Python, auditable)
│
├─ infra/
│  ├─ docker/             docker-compose dev stack (api + web + pg + redis)
│  └─ bicep/              Azure Container Apps deployment
│
├─ .github/
│  ├─ workflows/          ci-api, ci-web, ci-contracts, security-scans, release
│  ├─ CODEOWNERS
│  ├─ PULL_REQUEST_TEMPLATE.md
│  └─ ISSUE_TEMPLATE/
│
├─ docs/                  Developer docs
└─ ...                    SDLC paperwork folders (project_charter, risk_register,
                          test_strategy_and_test_plan, etc.)
```

## Quickstart

### Backend

```bash
cd enterprise_ai_backend
pip install -r requirements.txt
uvicorn app.main:app --reload                # http://127.0.0.1:8000/docs
python tests/test_backend.py                  # 116/116 assertions
```

For an HR-facing verification path, see `docs/hr-review-guide.md`.

### Frontend

```bash
cd apps/web
npm install
npm run dev                                   # http://127.0.0.1:5173
```

### Full local stack

```bash
docker compose -f infra/docker/docker-compose.yml up --build
```

## What's real, not mocked

| Piece | Library | Evidence |
|-------|---------|----------|
| Password hashing | `bcrypt` 4.x | `enterprise_ai_backend/app/security.py` |
| Tokens | `python-jose` HS256 JWT | same file |
| Database | SQLAlchemy 2.0 → SQLite / Postgres | `app/database.py` |
| ML | scikit-learn `IsolationForest` | `app/ml.py` — test outlier flagged `-1` |
| Reliability math | `math.exp(-t/MTBF)` etc. | `app/services.py`, verified to 1e-6 |
| SHA-256 | `hashlib` | `app/routers/hash.py`, verified byte-for-byte |

## CI/CD

Five GitHub Actions workflows:

1. `ci-api.yml` — runs the full integration test on py3.10/3.11/3.12 + builds Docker image
2. `ci-web.yml` — TypeScript typecheck + Vite build + Docker image
3. `ci-contracts.yml` — fails the PR if `libs/schemas/openapi.json` drifts or policy breaks
4. `security-scans.yml` — pip-audit, npm audit, gitleaks, CodeQL
5. `release.yml` — on tag `v*.*.*`: builds + pushes to GHCR, deploys Bicep to Azure

## Governance paperwork

The SDLC paperwork lives in the top-level folders (`project_charter/`,
`risk_register/`, `test_strategy_and_test_plan/`, `release_plan/`,
`security_and_compliance_plan/`, etc.). See `docs/README.md` for the
index, and `Project software development life cycle..txt` for the
canonical SDLC.

## HR review status

The codebase is structured for public review and live deployment. Current release evidence is tracked in:

- `docs/hr-review-guide.md`
- `docs/go-no-go.md`
- `docs/release-evidence.md`

The public Azure URL must be added after Azure CLI validation and deployment complete.

## Deploy to Azure

See `infra/bicep/README.md` and `Azure/Azure.txt` — resource naming
`rg-earp-<env>-<region>`, Key Vault-backed secrets, managed identity,
auto-scale 1–5 API replicas.

## Licence

Internal / pre-commercial. See `LICENSE` at the project root for the full
notice and `SECURITY.md` for vulnerability reporting.
