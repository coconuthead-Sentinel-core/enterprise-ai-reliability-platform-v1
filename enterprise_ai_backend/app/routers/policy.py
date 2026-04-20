"""Policy router: gate decisions on reliability scores (Sprint 3, E3-S1)
plus a policy-evaluation audit log (Sprint 3, E3-S3)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..schemas import PolicyGateDecision, PolicyGateInput, PolicyHistoryOut

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/evaluate", response_model=PolicyGateDecision)
def evaluate(
    payload: PolicyGateInput,
    db: Session = Depends(get_db),
):
    """Evaluate the policy gate on a reliability score input.

    The request body carries the same shape as ``POST /reliability/score``
    (a ``system_name`` + list of ``ReliabilityScoreComponent``) plus an
    optional ``thresholds`` override. The response is an ``allow`` /
    ``warn`` / ``block`` decision with a list of rationale ``reasons``,
    the applied thresholds (echoed), and the resolved composite score
    and tier.

    Sprint 3, E3-S3: every call is persisted as a
    :class:`database.PolicyEvaluationRecord` so
    ``GET /policy/history`` can return a trend over time without the
    caller having to re-submit the inputs.
    """
    return services.evaluate_policy_gate_from_input(payload, db=db)


@router.get("/history", response_model=PolicyHistoryOut)
def history(
    system_name: Optional[str] = Query(
        None,
        min_length=1,
        max_length=200,
        description="Filter the history to a single system (omit for all).",
    ),
    limit: int = Query(
        50, ge=1, le=500,
        description="Maximum number of records to return (newest first).",
    ),
    db: Session = Depends(get_db),
) -> PolicyHistoryOut:
    """Return the policy-evaluation audit log with trend statistics.

    Records are newest-first. ``stats`` reports count, latest / earliest
    decision + composite, per-decision counts and rates, rolling average
    / min / max composite, a ``trend_direction`` (improving / degrading
    / stable / insufficient_data) computed from composite scores, and a
    chronological list of every decision change in the window.
    """
    return services.policy_evaluation_history(
        db, system_name=system_name, limit=limit
    )
