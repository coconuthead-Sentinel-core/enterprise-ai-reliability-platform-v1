"""
Enterprise AI Reliability Platform (EARP) — FastAPI application entry point.

Run with:
    uvicorn src.main:app --reload

Startup loads all mock data into the EvidenceRegistryService so the API is
immediately usable without any prior POST requests.

Services wired:
    ConnectorGateway          — payload validation
    EvidenceRegistryService   — evidence store with lineage
    ReliabilityScoringService — weighted scoring engine
    PolicyEvaluationService   — gate decision engine
    AuditReportingService     — immutable audit export
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.evaluations import router, _evidence
from src.mock_data import (
    MOCK_RUN_1,
    MOCK_RUN_2,
    MOCK_RUN_3,
    MOCK_CONNECTOR_META_1,
    MOCK_CONNECTOR_META_2,
    MOCK_CONNECTOR_META_3,
)


# ---------------------------------------------------------------------------
# Lifespan handler — replaces deprecated @app.on_event("startup")
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan context manager.

    On startup: pre-loads the three mock evaluation runs into
    EvidenceRegistryService so the API is immediately usable.
    """
    mock_runs = [
        (MOCK_RUN_1, MOCK_CONNECTOR_META_1),
        (MOCK_RUN_2, MOCK_CONNECTOR_META_2),
        (MOCK_RUN_3, MOCK_CONNECTOR_META_3),
    ]

    loaded = 0
    for run, meta in mock_runs:
        if not _evidence.exists(run.evaluation_id):
            _evidence.register(run, connector_metadata=meta)
            loaded += 1

    print(f"[EARP] Startup complete — {loaded} mock evaluation run(s) loaded.")
    print(f"[EARP] Total registered runs: {_evidence.count()}")
    print("[EARP] API docs: http://127.0.0.1:8000/docs")

    yield  # Application runs here

    print("[EARP] Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Enterprise AI Reliability Platform (EARP)",
    description=(
        "Provides gate-controlled release readiness scoring, policy evaluation, "
        "evidence registry with lineage tracking, and immutable audit reporting "
        "for LLM model versions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------------

app.include_router(router)
