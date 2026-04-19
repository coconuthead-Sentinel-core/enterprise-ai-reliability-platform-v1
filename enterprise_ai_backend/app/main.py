"""EARP API — Enterprise AI Reliability Platform.

Provides endpoints for reliability scoring, sprint metadata,
and release-gate evaluation of LLM-powered systems.
"""

from fastapi import FastAPI

from enterprise_ai_backend.app.routers import info, reliability

app = FastAPI(
    title="EARP LLM Reliability API",
    version="0.3.0",
    description=(
        "Enterprise AI Reliability Platform API for LLM evaluation ingestion, "
        "reliability scoring, policy gate decisions, and audit export."
    ),
)

app.include_router(info.router)
app.include_router(reliability.router)


@app.get("/healthz", tags=["ops"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
