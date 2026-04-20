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
    ReliabilityScoreWithExplanation,
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


@router.post("/score/explain", response_model=ReliabilityScoreWithExplanation)
def score_explain(payload: ReliabilityScoreInput):
    """Composite reliability score + per-component explanation.

    Extends ``POST /reliability/score`` with an ``explanation`` object that
    identifies:

    * ``top_driver`` and ``top_gap`` components,
    * per-component contributions (absolute and percent of the composite),
    * distance to adjacent tier boundaries (``tier_gap``),
    * weakest / strongest NIST AI RMF function, and
    * a one-sentence plain-English recommendation.
    """
    return services.explain_reliability_score(payload)
