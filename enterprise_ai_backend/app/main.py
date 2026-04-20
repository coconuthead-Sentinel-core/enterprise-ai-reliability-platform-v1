"""FastAPI app entry - full build with auth, assessments, AI, and frontend mount."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .routers import ai, assessments, auth, hash as hash_router, health, info, policy, reliability

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Reliability Platform - Backend API (full build)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    os.makedirs("data", exist_ok=True)
    init_db()


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(reliability.router)
app.include_router(policy.router)
app.include_router(assessments.router)
app.include_router(ai.router)
app.include_router(hash_router.router)
app.include_router(info.router)


_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "ui": "/ui",
        "health": "/health",
    }
