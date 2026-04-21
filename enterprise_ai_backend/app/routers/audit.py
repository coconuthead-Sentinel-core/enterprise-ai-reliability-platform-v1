"""Audit router: append-only hash-chained audit history and verification."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import services
from ..database import User, get_db
from ..schemas import AuditChainVerificationOut, AuditLogHistoryOut
from ..security import require_roles

router = APIRouter(prefix="/audit", tags=["audit"])

_AUDIT_VIEWER = require_roles("admin", "security_lead", "compliance_lead")


@router.get("/history", response_model=AuditLogHistoryOut)
def history(
    event_type: Optional[str] = Query(
        None,
        min_length=1,
        max_length=100,
        description="Filter to one audit event type.",
    ),
    entity_type: Optional[str] = Query(
        None,
        min_length=1,
        max_length=100,
        description="Filter to one audited entity type.",
    ),
    entity_key: Optional[str] = Query(
        None,
        min_length=1,
        max_length=200,
        description="Filter to one audited entity key.",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of records to return (newest first).",
    ),
    _current: User = Depends(_AUDIT_VIEWER),
    db: Session = Depends(get_db),
) -> AuditLogHistoryOut:
    return services.audit_log_history(
        db,
        event_type=event_type,
        entity_type=entity_type,
        entity_key=entity_key,
        limit=limit,
    )


@router.get("/verify", response_model=AuditChainVerificationOut)
def verify(
    _current: User = Depends(_AUDIT_VIEWER),
    db: Session = Depends(get_db),
) -> AuditChainVerificationOut:
    return services.verify_audit_chain(db)
