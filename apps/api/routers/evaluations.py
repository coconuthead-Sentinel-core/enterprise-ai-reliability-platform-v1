import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import LLMEvaluationRun, LLMModelVersion, PromptSetVersion
from schemas import EvaluationRunCreate, EvaluationRunResponse

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.post("", response_model=EvaluationRunResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_evaluation(payload: EvaluationRunCreate, db: Session = Depends(get_db)):
    if not db.query(LLMModelVersion).filter(
        LLMModelVersion.model_id == payload.model_id
    ).first():
        raise HTTPException(status_code=400, detail="model_id not found")

    if not db.query(PromptSetVersion).filter(
        PromptSetVersion.prompt_set_id == payload.prompt_set_id
    ).first():
        raise HTTPException(status_code=400, detail="prompt_set_id not found")

    record = LLMEvaluationRun(
        evaluation_id=str(uuid.uuid4()),
        model_id=payload.model_id,
        model_version=payload.model_version,
        prompt_set_id=payload.prompt_set_id,
        prompt_set_version=payload.prompt_set_version,
        total_prompts=payload.total_prompts,
        successful_tasks=payload.successful_tasks,
        supported_claims=payload.supported_claims,
        unsupported_claims=payload.unsupported_claims,
        policy_violations=payload.policy_violations,
        p95_latency_ms=payload.p95_latency_ms,
        total_inference_cost_usd=payload.total_inference_cost_usd,
        prompt_robustness=payload.prompt_robustness,
        availability=payload.availability,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{evaluation_id}", response_model=EvaluationRunResponse)
def get_evaluation(evaluation_id: str, db: Session = Depends(get_db)):
    record = db.query(LLMEvaluationRun).filter(
        LLMEvaluationRun.evaluation_id == evaluation_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return record
