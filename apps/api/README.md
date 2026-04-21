# apps/api - EARP FastAPI backend signpost

The live, tested backend lives at:

```text
../../enterprise_ai_backend/
```

That is the canonical source of truth for the API.

## Endpoints (v0.3.0)

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/` | public | metadata |
| GET | `/health` | public | uptime + DB ping |
| POST | `/auth/register` | public | create user |
| POST | `/auth/login` | public | JWT access token |
| GET | `/auth/me` | bearer | current user |
| POST | `/reliability/compute` | public | MTBF/MTTR reliability math |
| POST | `/reliability/score` | public | weighted composite score |
| POST | `/reliability/score/explain` | public | score explanation |
| GET | `/reliability/score/history` | public | score history |
| POST | `/policy/evaluate` | public | policy gate |
| GET | `/policy/history` | public | policy audit history |
| GET | `/audit/history` | security/compliance/admin | audit ledger history |
| GET | `/audit/verify` | security/compliance/admin | audit-chain verification |
| GET | `/compliance/retention/policy` | security/compliance/admin | retention policy |
| POST | `/compliance/retention/policy` | security/compliance/admin | configure retention |
| GET | `/compliance/retention/status` | security/compliance/admin | retention/legal-hold status |
| POST | `/compliance/legal-holds` | security/compliance/admin | create legal hold |
| POST | `/compliance/legal-holds/{id}/release` | security/compliance/admin | release legal hold |
| GET | `/release/approvals/current` | bearer | release approval summary |
| POST | `/release/approvals/request` | bearer | create approval requests |
| POST | `/release/approvals/{id}/approve` | bearer | approve in the matching role lane |
| POST | `/assessments` | bearer | NIST AI RMF assessment |
| GET | `/assessments` | bearer | list assessments |
| GET | `/assessments/{id}` | bearer | single assessment |
| POST | `/ai/anomaly-detect` | bearer | `IsolationForest` on records |
| GET | `/ai/anomaly-detect/from-history` | bearer | `IsolationForest` on stored history |
| GET | `/dashboard/summary` | bearer | dashboard summary |
| GET | `/reports/executive-summary` | bearer | executive summary JSON |
| GET | `/reports/executive-summary.pdf` | bearer | executive summary PDF |
| POST | `/hash/sha256` | public | SHA-256 echo |

## Run locally

```bash
cd ../../enterprise_ai_backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Tests

```bash
cd ../../enterprise_ai_backend
python tests/test_backend.py
```

Current full integration result: `378/378` assertions passing.
