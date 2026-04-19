from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import engine, Base
from routers import model_versions, prompt_sets, evaluations, gates, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DDL only for local dev; production uses Alembic migrations
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
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
