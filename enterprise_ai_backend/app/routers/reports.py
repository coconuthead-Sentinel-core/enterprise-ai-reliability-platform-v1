"""Executive summary JSON + PDF export (Sprint 4 / Sprint 5 slice)."""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import User, get_db
from ..reporting import build_executive_summary, render_executive_summary_pdf
from ..schemas import ExecutiveSummaryOut
from ..security import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/executive-summary", response_model=ExecutiveSummaryOut)
def executive_summary(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ExecutiveSummaryOut:
    """Return the structured executive summary and evidence bundle."""
    return build_executive_summary(db, viewer_role=current.role)


@router.get("/executive-summary.pdf")
def executive_summary_pdf(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Response:
    """Render the executive summary as a downloadable PDF."""
    summary = build_executive_summary(db, viewer_role=current.role)
    pdf = render_executive_summary_pdf(summary)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="earp-executive-summary.pdf"'
            )
        },
    )
