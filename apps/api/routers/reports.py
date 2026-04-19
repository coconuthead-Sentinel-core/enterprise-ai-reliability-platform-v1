from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import GateDecision, LLMEvaluationRun
from schemas import AuditReportResponse

router = APIRouter(prefix="/reports", tags=["Audit Reports"])


@router.get("/audit/{decision_id}", response_model=AuditReportResponse)
def export_audit_report(decision_id: str, db: Session = Depends(get_db)):
    decision = db.query(GateDecision).filter(
        GateDecision.decision_id == decision_id
    ).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Gate decision not found")

    run = db.query(LLMEvaluationRun).filter(
        LLMEvaluationRun.evaluation_id == decision.evaluation_id
    ).first()

    return AuditReportResponse(
        decision_id=decision.decision_id,
        evaluation_id=decision.evaluation_id,
        policy_score=float(decision.policy_score),
        result=decision.result.value,
        rationale=decision.rationale,
        decided_at=decision.decided_at,
        model_id=run.model_id,
        model_version=run.model_version,
        prompt_set_id=run.prompt_set_id,
        prompt_set_version=run.prompt_set_version,
        generated_at=datetime.now(timezone.utc),
        report_uri=f"/reports/audit/{decision_id}",
    )
