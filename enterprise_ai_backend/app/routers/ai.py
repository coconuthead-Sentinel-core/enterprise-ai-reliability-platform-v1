"""AI endpoints - real scikit-learn IsolationForest anomaly detection."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ml
from ..database import User, get_db
from ..schemas import AnomalyInput, AnomalyOutput
from ..security import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/anomaly-detect", response_model=AnomalyOutput)
def detect(
    payload: AnomalyInput,
    current: User = Depends(get_current_user),
):
    try:
        result = ml.detect_anomalies(payload.records, payload.contamination)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return AnomalyOutput(**result)


@router.get("/anomaly-detect/from-history", response_model=AnomalyOutput)
def detect_from_history(
    contamination: float = 0.1,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    try:
        result = ml.detect_anomalies_from_history(db, contamination)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return AnomalyOutput(**result)
