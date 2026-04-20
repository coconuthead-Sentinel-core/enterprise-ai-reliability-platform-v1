"""Dashboard aggregation endpoints (Sprint 4)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import User, get_db
from ..reporting import build_dashboard_summary
from ..schemas import DashboardSummaryOut
from ..security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def summary(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> DashboardSummaryOut:
    """Return the role-aware dashboard summary for the current user."""
    return build_dashboard_summary(db, viewer_role=current.role)
