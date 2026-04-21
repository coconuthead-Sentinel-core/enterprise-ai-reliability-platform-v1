"""Release approval workflow with separated approver roles (Sprint 5, E5-S1)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import services
from ..database import User, get_db
from ..schemas import (
    ReleaseApprovalActionInput,
    ReleaseApprovalOut,
    ReleaseApprovalRequestInput,
    ReleaseApprovalSummaryOut,
)
from ..security import get_current_user
from . import info

router = APIRouter(prefix="/release", tags=["release"])


@router.get("/approvals/current", response_model=ReleaseApprovalSummaryOut)
def current_approvals(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ReleaseApprovalSummaryOut:
    sprint = info.current_sprint()
    return services.release_approval_summary(
        db,
        release=sprint.release,
        branch=sprint.branch,
    )


@router.post("/approvals/request", response_model=ReleaseApprovalSummaryOut)
def request_approvals(
    payload: ReleaseApprovalRequestInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ReleaseApprovalSummaryOut:
    sprint = info.current_sprint()
    return services.request_release_approvals(
        db,
        release=sprint.release,
        branch=sprint.branch,
        requested_by_email=current.email,
        request_notes=payload.request_notes,
    )


@router.post("/approvals/{approval_id}/approve", response_model=ReleaseApprovalOut)
def approve(
    approval_id: int,
    payload: ReleaseApprovalActionInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ReleaseApprovalOut:
    try:
        record = services.approve_release_approval(
            db,
            approval_id=approval_id,
            approver_email=current.email,
            approver_role=current.role,
            approval_notes=payload.approval_notes,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "not_found":
            raise HTTPException(status_code=404, detail="Release approval not found")
        if code == "already_approved":
            raise HTTPException(status_code=409, detail="Release approval already approved")
        if code == "self_approval_forbidden":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requester cannot approve their own release candidate",
            )
        if code == "wrong_role":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Matching approver role or admin role required",
            )
        raise
    return record
