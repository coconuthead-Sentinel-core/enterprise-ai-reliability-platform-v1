import sys
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

# libs/policy is a sibling of apps/api; add to path when running inside container/tests
_libs_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "libs")
if _libs_path not in sys.path:
    sys.path.insert(0, _libs_path)

from policy.scoring import compute_metrics  # noqa: E402
from policy.policy_engine import evaluate_gate_score  # noqa: E402
from models.evaluation_run import LLMEvaluationRun  # noqa: E402
from models.gate_decision import GateDecision, GateResult  # noqa: E402


def evaluate_gate(run: LLMEvaluationRun, policy_id: str, db: Session) -> GateDecision:
    metrics = compute_metrics(
        total_prompts=run.total_prompts,
        successful_tasks=run.successful_tasks,
        supported_claims=run.supported_claims,
        unsupported_claims=run.unsupported_claims,
        policy_violations=run.policy_violations,
        p95_latency_ms=run.p95_latency_ms,
        prompt_robustness=float(run.prompt_robustness),
        availability=float(run.availability),
    )

    score, result_str, rationale = evaluate_gate_score(metrics=metrics, policy_id=policy_id)

    decision = GateDecision(
        decision_id=str(uuid.uuid4()),
        evaluation_id=run.evaluation_id,
        policy_id=policy_id,
        policy_score=Decimal(str(round(score, 4))),
        result=GateResult(result_str),
        rationale=rationale,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision
