"""Reliability router: MTBF/MTTR math + weighted composite score (Sprint 2)."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..schemas import (
    ReliabilityInput,
    ReliabilityOutput,
    ReliabilityScoreInput,
    ReliabilityScoreOutput,
)

router = APIRouter(prefix="/reliability", tags=["reliability"])


@router.post("/compute", response_model=ReliabilityOutput)
def compute(payload: ReliabilityInput, db: Session = Depends(get_db)):
    """MTBF/MTTR/mission-time → availability, reliability, failure rate."""
    return services.compute_reliability(db, payload)


@router.get("/history", response_model=List[ReliabilityOutput])
def history(limit: int = 50, db: Session = Depends(get_db)):
    """Recent reliability computations, newest first."""
    return services.list_reliability(db, limit=limit)


@router.post("/score", response_model=ReliabilityScoreOutput)
def score(payload: ReliabilityScoreInput):
    """Weighted composite reliability score across multiple signals.

    Each component has a ``value`` in [0, 1] and a ``weight``. Components
    are combined into a single 0-100 composite score, placed into a tier
    (LOW/MEDIUM/HIGH), and optionally rolled up per NIST AI RMF function.
    """
    return services.compute_reliability_score(payload)
