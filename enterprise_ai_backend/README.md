# enterprise_ai_backend — Full Build (v0.2.0)

FastAPI backend for the Enterprise AI Reliability Platform v1.
Includes persistence, NIST AI RMF assessment scoring, a minimal front end,
integration tests with real numbers, and Docker deployment.

## Folder layout

```
enterprise_ai_backend/
├── app/                         # Python package - the real application
│   ├── __init__.py
│   ├── main.py                  # FastAPI app + CORS + startup
│   ├── config.py                # Loads .env into typed settings
│   ├── database.py              # SQLAlchemy engine + models
│   ├── schemas.py               # Pydantic request / response schemas
│   ├── services.py              # Middle layer - business logic
│   └── routers/
│       ├── health.py            # GET  /health
│       ├── reliability.py       # POST /reliability/compute, GET /history
│       ├── assessments.py       # CRUD on NIST AI RMF assessments
│       └── hash.py              # POST /hash/sha256
├── tests/
│   └── test_backend.py          # Real integration test (no mocks)
├── frontend/                    # Minimal vanilla-JS dashboard
│   ├── index.html               # served at  /ui
│   ├── app.js
│   └── styles.css
├── data/                        # SQLite DB lives here (gitignored)
├── main.py                      # Back-compat re-export
├── run.py                       # python run.py  -> starts uvicorn
├── test_backend.py              # python test_backend.py  shim
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env                         # Local secrets (gitignored)
├── .env.example                 # Template
├── .gitignore
└── README.md
```

## Setup (Windows PowerShell)

```powershell
cd "<path-to>\enterprise_ai_backend"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Setup (macOS / Linux)

```bash
cd <path-to>/enterprise_ai_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the real backend test (real numbers, no mocks)

```bash
python test_backend.py
```

Exercises every endpoint against a real SQLite database and real math:

| Check | What it verifies |
|-------|------------------|
| `GET /health` | Real uptime, real Python version, real DB round-trip |
| `POST /reliability/compute` (MTBF=1000, MTTR=4, mission=720) | availability 0.996016, reliability 0.486752, failure rate 0.001/hr, 0.72 expected failures — byte-exact against `math.exp(-720/1000)` |
| Second compute (MTBF=50000, MTTR=2, mission=8760) | Datacenter-grade annual reliability |
| `GET /reliability/history` | Real DB read-back of both computations |
| `POST /assessments` (scores 85/78/72/81) | overall = 79.0, tier = MEDIUM |
| Low-risk sample (95/90/88/92) | overall ≥ 80 → LOW |
| High-risk sample (40/55/50/45) | overall < 60 → HIGH |
| `GET /assessments/{id}` / 404 on missing | Real lookup + error paths |
| `POST /hash/sha256` | Matches Python's own `hashlib.sha256` |
| Validation errors | Negative MTBF, empty strings, scores > 100 all return 422 |

## Run the server

```bash
python run.py
```

Then open:

- **Swagger UI** — <http://localhost:8000/docs>
- **Front-end dashboard** — <http://localhost:8000/ui>
- **Root** — <http://localhost:8000/>

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App info |
| GET | `/health` | Real health + uptime + DB status |
| POST | `/reliability/compute` | MTBF/MTTR reliability math, persisted |
| GET | `/reliability/history` | List prior computations |
| POST | `/assessments` | Create NIST AI RMF assessment |
| GET | `/assessments` | List assessments |
| GET | `/assessments/{id}` | Retrieve one (404 if missing) |
| POST | `/hash/sha256` | SHA-256 of a real string |
| GET | `/docs` | Swagger UI |
| GET | `/ui` | Frontend dashboard |

## Deploy with Docker

```bash
docker compose up --build
```

The `data/` folder is bind-mounted so the SQLite DB survives restarts.

## NIST AI RMF scoring rules

Each assessment records four scores (0–100) for GOVERN, MAP, MEASURE, MANAGE.
`overall_score` is a weighted average (equal weights by default). Risk tier:

| Overall | Tier |
|---------|------|
| ≥ 80 | LOW |
| 60–79.99 | MEDIUM |
| < 60 | HIGH |

## Azure deployment (next step)

The Dockerfile and docker-compose.yml are ready for:

- **Azure App Service for Containers** — push the image, set env vars
- **Azure Container Apps** — single-container, auto-scale
- **Azure Key Vault** — replace `.env` with Key Vault secrets in production

See the companion Azure course notes in the parent repo for the exact deploy steps.
