"""Reliability router: MTBF/MTTR math + weighted composite score (Sprint 2)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..schemas import (
    ReliabilityInput,
    ReliabilityOutput,
    ReliabilityScoreHistoryOut,
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
def score(
    payload: ReliabilityScoreInput,
    db: Session = Depends(get_db),
):
    """Weighted composite reliability score across multiple signals.

    Each component has a ``value`` in [0, 1] and a ``weight``. Components
    are combined into a single 0-100 composite score, placed into a tier
    (LOW/MEDIUM/HIGH), and optionally rolled up per NIST AI RMF function.

    Each call is persisted (Sprint 2 E2-S3) so
    ``GET /reliability/score/history`` can trend it over time.
    """
    return services.compute_reliability_score(payload, db=db)


@router.post("/score/explain", response_model=ReliabilityScoreWithExplanation)
def score_explain(
    payload: ReliabilityScoreInput,
    db: Session = Depends(get_db),
):
    """Composite reliability score + per-component explanation.

    Extends ``POST /reliability/score`` with an ``explanation`` object that
    identifies:

    * ``top_driver`` and ``top_gap`` components,
    * per-component contributions (absolute and percent of the composite),
    * distance to adjacent tier boundaries (``tier_gap``),
    * weakest / strongest NIST AI RMF function, and
    * a one-sentence plain-English recommendation.

    Also persists the underlying score record (Sprint 2 E2-S3).
    """
    return services.explain_reliability_score(payload, db=db)


@router.get("/score/history", response_model=ReliabilityScoreHistoryOut)
def score_history(
    system_name: Optional[str] = Query(
        None,
        description="Filter by system name (exact match). Omit for all systems.",
    ),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return recent composite scores (newest first) plus trend stats.

    Populated automatically by every ``POST /reliability/score`` and
    ``POST /reliability/score/explain`` call. The ``stats`` object
    includes rolling average, min/max, a simple improving / degrading /
    stable trend classification, and any tier transitions.
    """
    return services.reliability_score_history(
        db, system_name=system_name, limit=limit
    )
