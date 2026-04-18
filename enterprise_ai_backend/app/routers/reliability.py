"""POST /reliability/compute   and   GET /reliability/history"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..schemas import ReliabilityInput, ReliabilityOutput

router = APIRouter(prefix="/reliability", tags=["reliability"])


@router.post("/compute", response_model=ReliabilityOutput)
def compute(payload: ReliabilityInput, db: Session = Depends(get_db)):
    return services.compute_reliability(db, payload)


@router.get("/history", response_model=List[ReliabilityOutput])
def history(limit: int = 50, db: Session = Depends(get_db)):
    return services.list_reliability(db, limit=limit)
