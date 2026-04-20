# enterprise_ai_backend - FastAPI backend (v0.3.0)

FastAPI backend for the Enterprise AI Reliability Platform v1. Includes auth,
reliability scoring, policy gating, assessment storage, anomaly detection,
dashboard/reporting endpoints, and PDF export.

## Setup

### Windows PowerShell

```powershell
cd "<path-to>\enterprise_ai_backend"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
cd <path-to>/enterprise_ai_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally

```bash
python run.py
```

Then open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## Primary endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | app metadata |
| GET | `/health` | health + uptime + DB status |
| POST | `/auth/register` | create user |
| POST | `/auth/login` | issue JWT |
| GET | `/auth/me` | current user |
| POST | `/reliability/compute` | MTBF/MTTR reliability math |
| POST | `/reliability/score` | weighted composite reliability score |
| POST | `/reliability/score/explain` | score explanation |
| GET | `/reliability/score/history` | score history + trend stats |
| POST | `/policy/evaluate` | policy gate decision |
| GET | `/policy/history` | policy audit log + stats |
| POST | `/assessments` | create NIST AI RMF assessment |
| GET | `/assessments` | list assessments |
| GET | `/assessments/{id}` | get single assessment |
| POST | `/ai/anomaly-detect` | `IsolationForest` on records |
| GET | `/ai/anomaly-detect/from-history` | `IsolationForest` on stored history |
| GET | `/dashboard/summary` | dashboard summary payload |
| GET | `/reports/executive-summary` | structured executive summary |
| GET | `/reports/executive-summary.pdf` | PDF export |
| POST | `/hash/sha256` | SHA-256 utility |

## Tests

```bash
python tests/test_backend.py
python -m pytest -q
python -m pip check
python scripts/export_openapi.py
```

Current local validation:

- `tests/test_backend.py`: 313/313 assertions passing
- `pytest -q`: 2 tests passing

## Notes

- SQLite is the local default.
- The code is PostgreSQL-ready through SQLAlchemy.
- Azure deployment is blocked by credentials, not by the subscription tier.
