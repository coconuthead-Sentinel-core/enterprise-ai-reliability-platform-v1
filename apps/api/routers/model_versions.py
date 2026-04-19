import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import LLMModelVersion
from schemas import ModelVersionCreate, ModelVersionResponse

router = APIRouter(prefix="/models/versions", tags=["Model Versions"])


@router.post("", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED)
def register_model_version(payload: ModelVersionCreate, db: Session = Depends(get_db)):
    record = LLMModelVersion(
        model_id=str(uuid.uuid4()),
        provider=payload.provider,
        model_name=payload.model_name,
        model_version=payload.model_version,
        registered_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{model_id}", response_model=ModelVersionResponse)
def get_model_version(model_id: str, db: Session = Depends(get_db)):
    record = db.query(LLMModelVersion).filter(LLMModelVersion.model_id == model_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")
    return record
