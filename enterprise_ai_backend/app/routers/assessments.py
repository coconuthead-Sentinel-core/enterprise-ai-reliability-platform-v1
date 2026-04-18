"""NIST AI RMF-aligned assessment endpoints (authenticated)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import services
from ..database import User, get_db
from ..schemas import AssessmentInput, AssessmentOutput
from ..security import get_current_user

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentOutput, status_code=201)
def create(
    payload: AssessmentInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return services.create_assessment(db, payload)


@router.get("", response_model=List[AssessmentOutput])
def list_all(
    limit: int = 50,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return services.list_assessments(db, limit=limit)


@router.get("/{assessment_id}", response_model=AssessmentOutput)
def get_one(
    assessment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    record = services.get_assessment(db, assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return record
