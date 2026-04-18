"""GET /health - real uptime, real platform info, real DB check."""
import platform
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas import HealthResponse

router = APIRouter(tags=["system"])

SERVER_START = time.time()


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    # Real DB round-trip
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:  # pragma: no cover - defensive
        db_status = f"error: {e}"

    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        app_env=settings.APP_ENV,
        app_version=settings.APP_VERSION,
        python_version=platform.python_version(),
        platform=platform.platform(),
        uptime_seconds=round(time.time() - SERVER_START, 3),
        server_time_utc=datetime.now(timezone.utc).isoformat(),
        database=db_status,
    )
