from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import LLMEvaluationRun, GateDecision
from schemas import GateEvaluationRequest, GateDecisionResponse
from services.policy import evaluate_gate

router = APIRouter(prefix="/gates", tags=["Gate Evaluation"])


@router.post("/evaluate", response_model=GateDecisionResponse, status_code=status.HTTP_200_OK)
def evaluate_release_gate(payload: GateEvaluationRequest, db: Session = Depends(get_db)):
    run = db.query(LLMEvaluationRun).filter(
        LLMEvaluationRun.evaluation_id == payload.evaluation_id
    ).first()
    if not run:
        raise HTTPException(status_code=422, detail="evaluation_id not found")

    decision = evaluate_gate(run=run, policy_id=payload.policy_id, db=db)
    return decision
