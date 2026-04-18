# apps/api — EARP FastAPI backend

The live, tested backend lives at:

    ../../enterprise_ai_backend/

That's the canonical source of truth for the API (real FastAPI app, real
SQLAlchemy models, real bcrypt + JWT, real scikit-learn IsolationForest).
This folder is a signpost in the monorepo layout called out in
`GitHub documentation/GitHub documentation.txt`.

## Endpoints (v0.3.0)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET  | `/`                                | public | metadata |
| GET  | `/health`                           | public | uptime + db ping |
| POST | `/auth/register`                    | public | create user (bcrypt) |
| POST | `/auth/login`                       | public | JWT access token |
| GET  | `/auth/me`                          | bearer | current user |
| POST | `/reliability/compute`              | public | MTBF/MTTR → availability, reliability |
| GET  | `/reliability/history`              | public | last computations |
| POST | `/assessments`                      | bearer | NIST AI RMF scoring |
| GET  | `/assessments`                      | bearer | list assessments |
| GET  | `/assessments/{id}`                 | bearer | single assessment |
| POST | `/ai/anomaly-detect`                | bearer | IsolationForest on records |
| GET  | `/ai/anomaly-detect/from-history`   | bearer | IsolationForest on stored history |
| POST | `/hash/sha256`                      | public | SHA-256 echo |

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
# -> 50/50 assertions passed
```
