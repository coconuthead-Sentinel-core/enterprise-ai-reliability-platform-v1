"""Reliability router — POST /reliability/score.

Implements Epic E2 (Reliability Scoring Engine) from the product backlog.
"""

from __future__ import annotations

from fastapi import APIRouter

from enterprise_ai_backend.app.models.reliability import (
    ReliabilityScoreRequest,
    ReliabilityScoreResponse,
)
from enterprise_ai_backend.app.services.scoring import compute_reliability_score

router = APIRouter(prefix="/reliability", tags=["reliability"])


@router.post("/score", response_model=ReliabilityScoreResponse)
async def score(request: ReliabilityScoreRequest) -> ReliabilityScoreResponse:
    """Compute composite reliability and policy scores.

    Accepts raw evaluation metrics and returns:
      • SDLC ReliabilityIndex (5-weight composite)
      • Readiness Policy Score (6-weight composite)
      • Gate outcome (pass / conditional / fail)
      • Hard-constraint violation details
      • NIST AI RMF 1.0 function mapping
    """
    return compute_reliability_score(request)
