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


# ---------- Reliability Score Explanation (Sprint 2, E2-S2) ----------

def _tier_gap(composite_100: float, tier: str) -> schemas.TierGap:
    """Distance (in composite points) to adjacent tiers.

    LOW has no tier-up; HIGH has no tier-down.
    """
    if tier == "LOW":
        return schemas.TierGap(
            current_tier=tier,
            next_tier_up=None,
            points_needed_up=None,
            next_tier_down="MEDIUM",
            points_buffer_down=round(composite_100 - _TIER_LOW_MIN, 4),
        )
    if tier == "MEDIUM":
        return schemas.TierGap(
            current_tier=tier,
            next_tier_up="LOW",
            points_needed_up=round(_TIER_LOW_MIN - composite_100, 4),
            next_tier_down="HIGH",
            points_buffer_down=round(composite_100 - _TIER_MEDIUM_MIN, 4),
        )
    # HIGH
    return schemas.TierGap(
        current_tier=tier,
        next_tier_up="MEDIUM",
        points_needed_up=round(_TIER_MEDIUM_MIN - composite_100, 4),
        next_tier_down=None,
        points_buffer_down=None,
    )


def _recommendation(
    tier: str,
    top_gap: Optional[schemas.ScoreContribution],
    weakest_fn: Optional[schemas.NISTFunction],
    tier_gap: schemas.TierGap,
) -> str:
    """One-sentence, plain-English suggestion for the system owner."""
    if top_gap is None:
        return f"Composite is in the {tier} tier; no components available to target."

    gap_name = top_gap.component_name
    fn_hint = (
        f" (NIST {weakest_fn.value})" if weakest_fn is not None else ""
    )

    if tier == "HIGH":
        return (
            f"System is in the HIGH-risk tier; raising '{gap_name}'{fn_hint} "
            f"would need roughly {tier_gap.points_needed_up} points to reach MEDIUM."
        )
    if tier == "MEDIUM":
        return (
            f"Focus on '{gap_name}'{fn_hint}; about {tier_gap.points_needed_up} "
            f"composite points still separate this system from the LOW-risk tier."
        )
    # LOW
    return (
        f"System is in the LOW-risk tier with a {tier_gap.points_buffer_down}-point "
        f"buffer; '{gap_name}'{fn_hint} is still the best place to harden further."
    )


def explain_reliability_score(
    payload: schemas.ReliabilityScoreInput,
) -> schemas.ReliabilityScoreWithExplanation:
    """Composite reliability score + per-component explanation.

    Wraps :func:`compute_reliability_score` and adds:

    * ``contributions`` - how much each component adds to the 0-100 composite,
      with both an absolute share (``contribution``) and a relative share
      (``contribution_percent``) across the whole score.
    * ``top_driver`` - the component pulling the composite up the most.
    * ``top_gap`` - the component with the lowest value (biggest upside).
    * ``tier_gap`` - how many points separate the current composite from the
      adjacent tier boundaries.
    * ``weakest_nist_function`` / ``strongest_nist_function`` - the NIST AI RMF
      functions with the lowest and highest per-function breakdown scores.
    * ``recommendation`` - a short, plain-English suggestion.
    """
    base = compute_reliability_score(payload)

    total_weight = sum(c.weight for c in payload.components)
    # ``compute_reliability_score`` already guarded against zero totals, but
    # keep a local fallback so this helper is safe in isolation.
    if total_weight <= 0:
        raise ValueError("Total component weight must be positive.")

    contributions: List[schemas.ScoreContribution] = []
    for c in payload.components:
        norm_w = c.weight / total_weight
        contribution = round(c.value * norm_w * 100.0, 4)
        if base.composite_score > 0:
            contribution_percent = round(
                contribution / base.composite_score * 100.0, 4
            )
        else:
            contribution_percent = 0.0
        contributions.append(
            schemas.ScoreContribution(
                component_name=c.name,
                value=c.value,
                weight=c.weight,
                contribution=contribution,
                contribution_percent=contribution_percent,
                nist_function=c.nist_function,
            )
        )

    # Sort highest contribution first so the UI can just render the list.
    contributions.sort(key=lambda x: x.contribution, reverse=True)

    top_driver = contributions[0] if contributions else None
    # The biggest improvement opportunity is the component whose value is
    # lowest; weight ties are broken by larger weight (bigger lever).
    top_gap: Optional[schemas.ScoreContribution] = None
    if contributions:
        top_gap = min(contributions, key=lambda x: (x.value, -x.weight))

    # Weakest / strongest NIST function across the breakdown.
    breakdown_items = [
        (fn, getattr(base.nist_breakdown, fn))
        for fn in ("govern", "map", "measure", "manage")
        if getattr(base.nist_breakdown, fn) is not None
    ]
    weakest_fn: Optional[schemas.NISTFunction] = None
    strongest_fn: Optional[schemas.NISTFunction] = None
    if breakdown_items:
        weakest_name = min(breakdown_items, key=lambda x: x[1])[0]
        strongest_name = max(breakdown_items, key=lambda x: x[1])[0]
        weakest_fn = schemas.NISTFunction(weakest_name)
        strongest_fn = schemas.NISTFunction(strongest_name)

    tier_gap = _tier_gap(base.composite_score, base.tier)
    recommendation = _recommendation(base.tier, top_gap, weakest_fn, tier_gap)

    explanation = schemas.ScoreExplanation(
        top_driver=top_driver,
        top_gap=top_gap,
        contributions=contributions,
        tier_gap=tier_gap,
        weakest_nist_function=weakest_fn,
        strongest_nist_function=strongest_fn,
        recommendation=recommendation,
    )

    return schemas.ReliabilityScoreWithExplanation(
        system_name=base.system_name,
        composite_score=base.composite_score,
        tier=base.tier,
        weights_normalized=base.weights_normalized,
        nist_breakdown=base.nist_breakdown,
        components=base.components,
        computed_at=base.computed_at,
        explanation=explanation,
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
