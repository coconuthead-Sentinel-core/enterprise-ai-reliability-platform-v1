"""Policy router: gate decisions on reliability scores (Sprint 3, E3-S1)."""
from fastapi import APIRouter

from .. import services
from ..schemas import PolicyGateDecision, PolicyGateInput

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/evaluate", response_model=PolicyGateDecision)
def evaluate(payload: PolicyGateInput):
    """Evaluate the policy gate on a reliability score input.

    The request body carries the same shape as ``POST /reliability/score``
    (a ``system_name`` + list of ``ReliabilityScoreComponent``) plus an
    optional ``thresholds`` override. The response is an ``allow`` /
    ``warn`` / ``block`` decision with a list of rationale ``reasons``,
    the applied thresholds (echoed), and the resolved composite score
    and tier.
    """
    return services.evaluate_policy_gate_from_input(payload)
