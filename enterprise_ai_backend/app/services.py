"""Middle layer - pure business logic + persistence helpers."""
import hashlib
import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from . import database, schemas


# ---------- Reliability ----------

def compute_reliability(
    db: Session,
    payload: schemas.ReliabilityInput,
) -> database.ReliabilityComputation:
    availability = payload.mtbf_hours / (payload.mtbf_hours + payload.mttr_hours)
    failure_rate = 1.0 / payload.mtbf_hours
    reliability = math.exp(-payload.mission_time_hours / payload.mtbf_hours)
    expected_failures = payload.mission_time_hours / payload.mtbf_hours

    record = database.ReliabilityComputation(
        mtbf_hours=payload.mtbf_hours,
        mttr_hours=payload.mttr_hours,
        mission_time_hours=payload.mission_time_hours,
        availability=round(availability, 8),
        reliability=round(reliability, 8),
        failure_rate_per_hour=round(failure_rate, 10),
        expected_failures=round(expected_failures, 8),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_reliability(db: Session, limit: int = 50):
    return (
        db.query(database.ReliabilityComputation)
        .order_by(database.ReliabilityComputation.id.desc())
        .limit(limit)
        .all()
    )


# ---------- Reliability Score (Sprint 2, E2-S1) ----------

# Tier thresholds on the 0-100 composite scale. Matches the risk_tier()
# thresholds used for NIST AI RMF assessments so the two surfaces stay
# consistent.
_TIER_LOW_MIN = 80.0
_TIER_MEDIUM_MIN = 60.0


def _tier_from_composite(composite_100: float) -> str:
    if composite_100 >= _TIER_LOW_MIN:
        return "LOW"
    if composite_100 >= _TIER_MEDIUM_MIN:
        return "MEDIUM"
    return "HIGH"


def _weighted_avg(pairs: List[Tuple[float, float]]) -> Optional[float]:
    """Weighted average of (value, weight) pairs, scaled to 0-100.

    Returns None if the list is empty or weights sum to 0.
    """
    if not pairs:
        return None
    total_w = sum(w for _, w in pairs)
    if total_w <= 0:
        return None
    return round(sum(v * w for v, w in pairs) / total_w * 100.0, 4)


def compute_reliability_score(
    payload: schemas.ReliabilityScoreInput,
) -> schemas.ReliabilityScoreOutput:
    """Weighted composite reliability score + NIST AI RMF breakdown.

    * Each component contributes ``value * weight``.
    * If input weights do not sum to 1.0, they are normalized by the total.
    * The composite is returned on a 0-100 scale (internally 0-1).
    * Components tagged with a ``nist_function`` are grouped and
      reported as a per-function weighted average in the breakdown.
    """
    components = payload.components
    total_weight = sum(c.weight for c in components)
    if total_weight <= 0:
        # Should not happen because each component.weight is `gt=0`, but
        # guard against float underflow anyway.
        raise ValueError("Total component weight must be positive.")

    weights_normalized = not math.isclose(total_weight, 1.0, abs_tol=1e-6)

    composite_01 = sum(c.value * c.weight for c in components) / total_weight
    composite_100 = round(composite_01 * 100.0, 4)
    tier = _tier_from_composite(composite_100)

    by_function: dict = {
        "govern": [],
        "map": [],
        "measure": [],
        "manage": [],
    }
    for c in components:
        if c.nist_function is not None:
            by_function[c.nist_function.value].append((c.value, c.weight))

    breakdown = schemas.NISTBreakdown(
        govern=_weighted_avg(by_function["govern"]),
        map=_weighted_avg(by_function["map"]),
        measure=_weighted_avg(by_function["measure"]),
        manage=_weighted_avg(by_function["manage"]),
    )

    return schemas.ReliabilityScoreOutput(
        system_name=payload.system_name,
        composite_score=composite_100,
        tier=tier,
        weights_normalized=weights_normalized,
        nist_breakdown=breakdown,
        components=components,
        computed_at=datetime.now(timezone.utc),
    )


# ---------- Hash ----------

def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------- Assessments (NIST AI RMF) ----------

# Shared policy - re-exported from libs/policy/scoring.py too.
FUNCTION_WEIGHTS = {
    "govern": 0.25,
    "map": 0.25,
    "measure": 0.25,
    "manage": 0.25,
}


def risk_tier(overall: float) -> str:
    if overall >= 80:
        return "LOW"
    if overall >= 60:
        return "MEDIUM"
    return "HIGH"


def create_assessment(
    db: Session,
    payload: schemas.AssessmentInput,
) -> database.Assessment:
    overall = (
        payload.govern_score * FUNCTION_WEIGHTS["govern"]
        + payload.map_score * FUNCTION_WEIGHTS["map"]
        + payload.measure_score * FUNCTION_WEIGHTS["measure"]
        + payload.manage_score * FUNCTION_WEIGHTS["manage"]
    )
    record = database.Assessment(
        system_name=payload.system_name,
        owner=payload.owner,
        govern_score=payload.govern_score,
        map_score=payload.map_score,
        measure_score=payload.measure_score,
        manage_score=payload.manage_score,
        overall_score=round(overall, 4),
        risk_tier=risk_tier(overall),
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_assessments(db: Session, limit: int = 50):
    return (
        db.query(database.Assessment)
        .order_by(database.Assessment.id.desc())
        .limit(limit)
        .all()
    )


def get_assessment(db: Session, assessment_id: int) -> Optional[database.Assessment]:
    return db.query(database.Assessment).filter_by(id=assessment_id).first()
