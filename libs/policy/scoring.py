"""NIST AI RMF scoring policy.

Single source of truth for:
  * the four-function weights (GOVERN, MAP, MEASURE, MANAGE)
  * the risk-tier thresholds (LOW / MEDIUM / HIGH)

The backend imports these (indirectly, via ``app.services``). Any
dashboard, report, or CLI that needs to replicate scoring should
import from here instead of re-deriving thresholds.

This keeps policy decoupled from API code so compliance reviewers
can audit a single ~30-line file.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

RiskTier = Literal["LOW", "MEDIUM", "HIGH"]

FUNCTION_WEIGHTS: Dict[str, float] = {
    "govern": 0.25,
    "map": 0.25,
    "measure": 0.25,
    "manage": 0.25,
}

THRESHOLD_LOW = 80.0   # overall >= 80 -> LOW risk
THRESHOLD_MED = 60.0   # overall >= 60 -> MEDIUM risk, else HIGH


@dataclass(frozen=True)
class AssessmentInput:
    govern: float
    map: float
    measure: float
    manage: float


def overall_score(inp: AssessmentInput) -> float:
    """Weighted 0-100 score from the four NIST AI RMF function scores."""
    s = (
        inp.govern * FUNCTION_WEIGHTS["govern"]
        + inp.map * FUNCTION_WEIGHTS["map"]
        + inp.measure * FUNCTION_WEIGHTS["measure"]
        + inp.manage * FUNCTION_WEIGHTS["manage"]
    )
    # clamp to [0, 100] so policy stays monotonic even on bad inputs
    return max(0.0, min(100.0, float(s)))


def risk_tier(overall: float) -> RiskTier:
    if overall >= THRESHOLD_LOW:
        return "LOW"
    if overall >= THRESHOLD_MED:
        return "MEDIUM"
    return "HIGH"


__all__ = [
    "FUNCTION_WEIGHTS",
    "THRESHOLD_LOW",
    "THRESHOLD_MED",
    "AssessmentInput",
    "overall_score",
    "risk_tier",
]
