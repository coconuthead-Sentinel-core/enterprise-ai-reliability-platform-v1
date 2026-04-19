from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import engine, Base
from routers import model_versions, prompt_sets, evaluations, gates, reports

# Create tables on startup (migrations handle this in production via Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EARP LLM Reliability API",
    version="1.1.0",
    description="API for LLM evaluation ingestion, policy gate decisions, and audit export.",
)

app.include_router(model_versions.router, prefix="/v1")
app.include_router(prompt_sets.router, prefix="/v1")
app.include_router(evaluations.router, prefix="/v1")
app.include_router(gates.router, prefix="/v1")
app.include_router(reports.router, prefix="/v1")


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})
