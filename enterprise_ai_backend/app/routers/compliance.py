"""Compliance router: retention policy and legal-hold controls."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import services
from ..database import User, get_db
from ..schemas import (
    LegalHoldInput,
    LegalHoldOut,
    LegalHoldReleaseInput,
    RetentionPolicyInput,
    RetentionPolicyOut,
    RetentionStatusOut,
)
from ..security import require_roles

router = APIRouter(prefix="/compliance", tags=["compliance"])

_COMPLIANCE_OPERATOR = require_roles("admin", "security_lead", "compliance_lead")


@router.get("/retention/policy", response_model=RetentionPolicyOut)
def get_policy(
    _current: User = Depends(_COMPLIANCE_OPERATOR),
    db: Session = Depends(get_db),
) -> RetentionPolicyOut:
    return services.current_retention_policy(db)


@router.post("/retention/policy", response_model=RetentionPolicyOut)
def set_policy(
    payload: RetentionPolicyInput,
    current: User = Depends(_COMPLIANCE_OPERATOR),
    db: Session = Depends(get_db),
) -> RetentionPolicyOut:
    return services.set_retention_policy(
        db,
        retention_days=payload.retention_days,
        configured_by_email=current.email,
        notes=payload.notes,
    )


@router.get("/retention/status", response_model=RetentionStatusOut)
def retention_status(
    _current: User = Depends(_COMPLIANCE_OPERATOR),
    db: Session = Depends(get_db),
) -> RetentionStatusOut:
    return services.retention_status(db)


@router.post("/legal-holds", response_model=LegalHoldOut)
def create_hold(
    payload: LegalHoldInput,
    current: User = Depends(_COMPLIANCE_OPERATOR),
    db: Session = Depends(get_db),
) -> LegalHoldOut:
    try:
        return services.create_legal_hold(
            db,
            entity_type=payload.entity_type,
            entity_key=payload.entity_key,
            reason=payload.reason,
            created_by_email=current.email,
        )
    except ValueError as exc:
        if str(exc) == "active_hold_exists":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Active legal hold already exists for this entity",
            )
        raise


@router.post("/legal-holds/{hold_id}/release", response_model=LegalHoldOut)
def release_hold(
    hold_id: int,
    payload: LegalHoldReleaseInput,
    current: User = Depends(_COMPLIANCE_OPERATOR),
    db: Session = Depends(get_db),
) -> LegalHoldOut:
    try:
        return services.release_legal_hold(
            db,
            hold_id=hold_id,
            released_by_email=current.email,
            release_notes=payload.release_notes,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "not_found":
            raise HTTPException(status_code=404, detail="Legal hold not found")
        if code == "already_released":
            raise HTTPException(status_code=409, detail="Legal hold already released")
        raise
