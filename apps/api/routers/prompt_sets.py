import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import PromptSetVersion
from schemas import PromptSetCreate, PromptSetResponse

router = APIRouter(prefix="/prompt-sets", tags=["Prompt Sets"])


@router.post("", response_model=PromptSetResponse, status_code=status.HTTP_201_CREATED)
def register_prompt_set(payload: PromptSetCreate, db: Session = Depends(get_db)):
    record = PromptSetVersion(
        prompt_set_id=str(uuid.uuid4()),
        prompt_set_version=payload.prompt_set_version,
        benchmark_suite_id=payload.benchmark_suite_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{prompt_set_id}", response_model=PromptSetResponse)
def get_prompt_set(prompt_set_id: str, db: Session = Depends(get_db)):
    record = db.query(PromptSetVersion).filter(
        PromptSetVersion.prompt_set_id == prompt_set_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prompt set not found")
    return record
