"""Middle layer - pure business logic + persistence helpers."""
import hashlib
import json
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
    db: Optional[Session] = None,
) -> schemas.ReliabilityScoreOutput:
    """Weighted composite reliability score + NIST AI RMF breakdown.

    * Each component contributes ``value * weight``.
    * If input weights do not sum to 1.0, they are normalized by the total.
    * The composite is returned on a 0-100 scale (internally 0-1).
    * Components tagged with a ``nist_function`` are grouped and
      reported as a per-function weighted average in the breakdown.
    * When a SQLAlchemy ``Session`` is provided, the result is also
      persisted as a :class:`database.ReliabilityScoreRecord` so the
      ``GET /reliability/score/history`` endpoint can trend over time.
      Passing ``db=None`` keeps the function purely functional (useful
      for unit tests).
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

    output = schemas.ReliabilityScoreOutput(
        system_name=payload.system_name,
        composite_score=composite_100,
        tier=tier,
        weights_normalized=weights_normalized,
        nist_breakdown=breakdown,
        components=components,
        computed_at=datetime.now(timezone.utc),
    )

    if db is not None:
        _persist_score_record(db, output)

    return output


def _persist_score_record(
    db: Session,
    output: schemas.ReliabilityScoreOutput,
) -> database.ReliabilityScoreRecord:
    """Store one score result so history can trend it later."""
    record = database.ReliabilityScoreRecord(
        system_name=output.system_name,
        composite_score=output.composite_score,
        tier=output.tier,
        weights_normalized=1 if output.weights_normalized else 0,
        components_json=json.dumps(
            [c.model_dump(mode="json") for c in output.components]
        ),
        nist_govern=output.nist_breakdown.govern,
        nist_map=output.nist_breakdown.map,
        nist_measure=output.nist_breakdown.measure,
        nist_manage=output.nist_breakdown.manage,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


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
    db: Optional[Session] = None,
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

    When a ``Session`` is provided the underlying score is persisted
    exactly once (via ``compute_reliability_score``) so the explain
    endpoint also feeds ``GET /reliability/score/history``.
    """
    base = compute_reliability_score(payload, db=db)

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


# ---------- Reliability Score History (Sprint 2, E2-S3) ----------

def list_score_history(
    db: Session,
    system_name: Optional[str] = None,
    limit: int = 50,
) -> List[database.ReliabilityScoreRecord]:
    """Return score records newest-first, optionally filtered by system."""
    q = db.query(database.ReliabilityScoreRecord)
    if system_name is not None:
        q = q.filter(database.ReliabilityScoreRecord.system_name == system_name)
    q = q.order_by(database.ReliabilityScoreRecord.created_at.desc(),
                   database.ReliabilityScoreRecord.id.desc())
    return q.limit(limit).all()


def _trend_direction(scores_newest_first: List[float]) -> str:
    """Classify a trend as improving / degrading / stable.

    Compares the mean of the newer half against the mean of the older
    half. Anything under 2 data points is ``insufficient_data``.
    """
    n = len(scores_newest_first)
    if n < 2:
        return "insufficient_data"

    # Chronological order (oldest first) for readability.
    chrono = list(reversed(scores_newest_first))
    mid = n // 2
    older = chrono[:mid] if mid > 0 else chrono[:1]
    newer = chrono[mid:] if n - mid > 0 else chrono[-1:]
    older_mean = sum(older) / len(older)
    newer_mean = sum(newer) / len(newer)
    delta = newer_mean - older_mean

    # A swing of less than ~1 composite point reads as noise.
    if abs(delta) < 1.0:
        return "stable"
    return "improving" if delta > 0 else "degrading"


def score_trend_stats(
    records: List[database.ReliabilityScoreRecord],
) -> schemas.ScoreTrendStats:
    """Compute aggregate trend stats from a newest-first record list."""
    if not records:
        return schemas.ScoreTrendStats(
            count=0,
            trend_direction="insufficient_data",
            tier_transitions=[],
        )

    scores = [r.composite_score for r in records]
    # Records are newest-first; chronological view is reversed.
    chrono = list(reversed(records))

    transitions: List[schemas.TierTransition] = []
    for prev, curr in zip(chrono, chrono[1:]):
        if prev.tier != curr.tier:
            transitions.append(
                schemas.TierTransition(
                    from_tier=prev.tier,
                    to_tier=curr.tier,
                    at=curr.created_at,
                    composite_score=curr.composite_score,
                )
            )

    return schemas.ScoreTrendStats(
        count=len(records),
        latest_score=records[0].composite_score,
        latest_tier=records[0].tier,
        earliest_score=records[-1].composite_score,
        earliest_tier=records[-1].tier,
        rolling_average=round(sum(scores) / len(scores), 4),
        min_score=min(scores),
        max_score=max(scores),
        trend_direction=_trend_direction(scores),
        tier_transitions=transitions,
    )


def reliability_score_history(
    db: Session,
    system_name: Optional[str] = None,
    limit: int = 50,
) -> schemas.ReliabilityScoreHistoryOut:
    """End-to-end: query records + compute trend stats + wrap response."""
    records = list_score_history(db, system_name=system_name, limit=limit)
    stats = score_trend_stats(records)
    return schemas.ReliabilityScoreHistoryOut(
        system_name=system_name,
        stats=stats,
        records=[schemas.ReliabilityScoreRecordOut.model_validate(r) for r in records],
    )


# ---------- Policy Gate (Sprint 3, E3-S1) ----------

_SEVERITY_ORDER = {
    schemas.PolicySeverity.block: 0,
    schemas.PolicySeverity.warn: 1,
    schemas.PolicySeverity.info: 2,
}


def _overall_decision(
    reasons: List[schemas.PolicyReason],
) -> schemas.PolicyDecision:
    """Worst severity wins: any block -> block, else any warn -> warn, else allow."""
    severities = {r.severity for r in reasons}
    if schemas.PolicySeverity.block in severities:
        return schemas.PolicyDecision.block
    if schemas.PolicySeverity.warn in severities:
        return schemas.PolicyDecision.warn
    return schemas.PolicyDecision.allow


def evaluate_policy_gate(
    score: schemas.ReliabilityScoreOutput,
    thresholds: Optional[schemas.PolicyThresholds] = None,
) -> schemas.PolicyGateDecision:
    """Run the gate rules on an already-computed score.

    Rules (in order):
    1. Composite-score band (allow / warn / block)
    2. Per-NIST-function floor (``min_nist_function_score``)

    Any rule whose severity is ``block`` forces the overall decision to
    ``block``. Multiple reasons can fire in a single evaluation.
    """
    thresholds = thresholds or schemas.PolicyThresholds()
    reasons: List[schemas.PolicyReason] = []

    # --- Composite band ----------------------------------------------------
    c = score.composite_score
    if c >= thresholds.allow_min_composite:
        reasons.append(
            schemas.PolicyReason(
                code="composite_meets_allow",
                message=(
                    f"Composite score {c} meets the allow threshold "
                    f"({thresholds.allow_min_composite})."
                ),
                severity=schemas.PolicySeverity.info,
            )
        )
    elif c >= thresholds.warn_min_composite:
        reasons.append(
            schemas.PolicyReason(
                code="composite_below_allow",
                message=(
                    f"Composite score {c} is below the allow threshold "
                    f"({thresholds.allow_min_composite}); warn band."
                ),
                severity=schemas.PolicySeverity.warn,
            )
        )
    else:
        reasons.append(
            schemas.PolicyReason(
                code="composite_below_warn",
                message=(
                    f"Composite score {c} is below the warn threshold "
                    f"({thresholds.warn_min_composite}); block."
                ),
                severity=schemas.PolicySeverity.block,
            )
        )

    # --- NIST function floor ----------------------------------------------
    for fn in ("govern", "map", "measure", "manage"):
        val = getattr(score.nist_breakdown, fn)
        if val is None:
            continue
        if val < thresholds.min_nist_function_score:
            reasons.append(
                schemas.PolicyReason(
                    code=f"nist_{fn}_below_floor",
                    message=(
                        f"NIST {fn} score {val} is below the required "
                        f"minimum ({thresholds.min_nist_function_score})."
                    ),
                    severity=schemas.PolicySeverity.block,
                )
            )

    # Sort reasons by severity (block first, then warn, then info) so the
    # UI can render them top-to-bottom without re-sorting.
    reasons.sort(key=lambda r: _SEVERITY_ORDER[r.severity])

    decision = _overall_decision(reasons)

    return schemas.PolicyGateDecision(
        system_name=score.system_name,
        decision=decision,
        composite_score=score.composite_score,
        tier=score.tier,
        reasons=reasons,
        thresholds_applied=thresholds,
        evaluated_at=datetime.now(timezone.utc),
    )


def evaluate_policy_gate_from_input(
    payload: schemas.PolicyGateInput,
    db: Optional[Session] = None,
) -> schemas.PolicyGateDecision:
    """Compute the underlying reliability score (without persisting) and gate it.

    When a SQLAlchemy ``Session`` is provided (Sprint 3, E3-S3), the gate
    decision is also persisted as a
    :class:`database.PolicyEvaluationRecord` so ``GET /policy/history``
    can trend decisions over time. The score itself is *not* persisted
    here (we do not want a ``/policy/evaluate`` call to pollute the
    reliability score history); only the gate outcome is logged.
    """
    # ``db=None`` on compute_reliability_score keeps the score side-effect
    # free -- the policy audit log is a separate table.
    score = compute_reliability_score(payload.score_input, db=None)
    decision = evaluate_policy_gate(score, payload.thresholds)
    if db is not None:
        _persist_policy_evaluation(db, payload.score_input, decision)
    return decision


# ---------- Policy Audit Log (Sprint 3, E3-S3) ----------

def _persist_policy_evaluation(
    db: Session,
    score_input: schemas.ReliabilityScoreInput,
    decision: schemas.PolicyGateDecision,
) -> database.PolicyEvaluationRecord:
    """Store one gate decision so ``GET /policy/history`` can trend it."""
    record = database.PolicyEvaluationRecord(
        system_name=decision.system_name,
        decision=decision.decision.value,
        composite_score=decision.composite_score,
        tier=decision.tier,
        thresholds_json=decision.thresholds_applied.model_dump_json(),
        reasons_json=json.dumps(
            [r.model_dump(mode="json") for r in decision.reasons]
        ),
        score_input_json=score_input.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_policy_history(
    db: Session,
    system_name: Optional[str] = None,
    limit: int = 50,
) -> List[database.PolicyEvaluationRecord]:
    """Return policy evaluation records newest-first, optionally filtered."""
    q = db.query(database.PolicyEvaluationRecord)
    if system_name is not None:
        q = q.filter(database.PolicyEvaluationRecord.system_name == system_name)
    q = q.order_by(
        database.PolicyEvaluationRecord.created_at.desc(),
        database.PolicyEvaluationRecord.id.desc(),
    )
    return q.limit(limit).all()


def policy_trend_stats(
    records: List[database.PolicyEvaluationRecord],
) -> schemas.PolicyTrendStats:
    """Compute aggregate policy-trend stats from a newest-first record list.

    * Counts + rates for each ``allow`` / ``warn`` / ``block`` outcome.
    * Composite min / max / rolling average across the window.
    * ``trend_direction`` is classified from composite scores (reuses
      :func:`_trend_direction`) so the same "improving / degrading /
      stable" language carries across ``/reliability/score/history`` and
      ``/policy/history``.
    * ``decision_transitions`` lists every place the outcome changed,
      in chronological order.
    """
    if not records:
        return schemas.PolicyTrendStats(
            count=0,
            trend_direction="insufficient_data",
            decision_transitions=[],
        )

    scores = [r.composite_score for r in records]
    # Records are newest-first; chronological view is reversed.
    chrono = list(reversed(records))

    allow_count = sum(1 for r in records if r.decision == "allow")
    warn_count = sum(1 for r in records if r.decision == "warn")
    block_count = sum(1 for r in records if r.decision == "block")
    n = len(records)

    transitions: List[schemas.PolicyDecisionTransition] = []
    for prev, curr in zip(chrono, chrono[1:]):
        if prev.decision != curr.decision:
            transitions.append(
                schemas.PolicyDecisionTransition(
                    from_decision=schemas.PolicyDecision(prev.decision),
                    to_decision=schemas.PolicyDecision(curr.decision),
                    at=curr.created_at,
                    composite_score=curr.composite_score,
                )
            )

    return schemas.PolicyTrendStats(
        count=n,
        latest_decision=schemas.PolicyDecision(records[0].decision),
        latest_composite=records[0].composite_score,
        earliest_decision=schemas.PolicyDecision(records[-1].decision),
        earliest_composite=records[-1].composite_score,
        allow_count=allow_count,
        warn_count=warn_count,
        block_count=block_count,
        allow_rate=round(allow_count / n, 4),
        warn_rate=round(warn_count / n, 4),
        block_rate=round(block_count / n, 4),
        rolling_average_composite=round(sum(scores) / n, 4),
        min_composite=min(scores),
        max_composite=max(scores),
        trend_direction=_trend_direction(scores),
        decision_transitions=transitions,
    )


def policy_evaluation_history(
    db: Session,
    system_name: Optional[str] = None,
    limit: int = 50,
) -> schemas.PolicyHistoryOut:
    """End-to-end: query records + compute trend stats + wrap response."""
    records = list_policy_history(db, system_name=system_name, limit=limit)
    stats = policy_trend_stats(records)
    return schemas.PolicyHistoryOut(
        system_name=system_name,
        stats=stats,
        records=[
            schemas.PolicyEvaluationRecordOut.model_validate(r)
            for r in records
        ],
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


def _assessment_score_input(
    payload: schemas.AssessmentInput,
) -> schemas.ReliabilityScoreInput:
    """Project a NIST-RMF assessment into the reliability-score engine.

    Each of the four function scores (0-100 integer) becomes one
    :class:`schemas.ReliabilityScoreComponent` on the 0.0-1.0 scale, tagged
    with its NIST function and weighted equally (same weights used by
    ``create_assessment`` for ``overall_score``). This keeps the gate
    decision mathematically in sync with the assessment's own risk tier.
    """
    by_name = {
        "govern": payload.govern_score,
        "map": payload.map_score,
        "measure": payload.measure_score,
        "manage": payload.manage_score,
    }
    components = [
        schemas.ReliabilityScoreComponent(
            name=name,
            value=by_name[name] / 100.0,
            weight=FUNCTION_WEIGHTS[name],
            nist_function=schemas.NISTFunction(name),
        )
        for name in ("govern", "map", "measure", "manage")
    ]
    return schemas.ReliabilityScoreInput(
        system_name=payload.system_name,
        components=components,
    )


def gate_assessment(
    payload: schemas.AssessmentInput,
) -> schemas.PolicyGateDecision:
    """Run the default policy gate against an assessment payload.

    Sprint 3, E3-S2: ``create_assessment`` calls this and persists the
    result alongside the assessment record so ``risk_tier`` and the
    gate decision are always computed from the same numbers.
    """
    score_input = _assessment_score_input(payload)
    gate_input = schemas.PolicyGateInput(
        score_input=score_input, thresholds=None
    )
    return evaluate_policy_gate_from_input(gate_input)


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
    gate = gate_assessment(payload)
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
        gate_decision=gate.decision.value,
        gate_reasons_json=json.dumps(
            [r.model_dump(mode="json") for r in gate.reasons]
        ),
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
