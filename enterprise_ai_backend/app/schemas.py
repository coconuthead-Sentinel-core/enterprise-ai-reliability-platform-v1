"""Pydantic request / response schemas."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------- Auth ----------

class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=8, max_length=200)

    @field_validator("email")
    @classmethod
    def _looks_like_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@", 1)[-1]:
            raise ValueError("email must contain '@' and a domain")
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str
    created_at: datetime


class ReleaseApprovalType(str, Enum):
    security_lead = "security_lead"
    compliance_lead = "compliance_lead"


class ReleaseApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"


class ReleaseApprovalRequestInput(BaseModel):
    request_notes: Optional[str] = Field(default=None, max_length=2000)


class ReleaseApprovalActionInput(BaseModel):
    approval_notes: Optional[str] = Field(default=None, max_length=2000)


class ReleaseApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    release: str
    branch: str
    approval_type: ReleaseApprovalType
    status: ReleaseApprovalStatus
    requested_by_email: str
    approved_by_email: Optional[str] = None
    request_notes: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None


class ReleaseApprovalSummaryOut(BaseModel):
    release: str
    branch: str
    ready_for_release: bool
    pending_approval_types: List[ReleaseApprovalType] = Field(default_factory=list)
    approvals: List[ReleaseApprovalOut] = Field(default_factory=list)


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_env: str
    app_version: str
    python_version: str
    platform: str
    uptime_seconds: float
    server_time_utc: str
    database: str


# ---------- Reliability ----------

class ReliabilityInput(BaseModel):
    mtbf_hours: float = Field(..., gt=0)
    mttr_hours: float = Field(..., gt=0)
    mission_time_hours: float = Field(..., gt=0)


class ReliabilityOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    mtbf_hours: float
    mttr_hours: float
    mission_time_hours: float
    availability: float
    reliability: float
    failure_rate_per_hour: float
    expected_failures: float
    created_at: datetime


# ---------- Reliability Score (Sprint 2, E2-S1) ----------

class NISTFunction(str, Enum):
    """NIST AI RMF 1.0 functions."""

    govern = "govern"
    map = "map"
    measure = "measure"
    manage = "manage"


class ReliabilityScoreComponent(BaseModel):
    """One input signal to the weighted reliability score."""

    name: str = Field(..., min_length=1, max_length=100)
    value: float = Field(
        ..., ge=0.0, le=1.0,
        description="Normalized component value between 0.0 and 1.0.",
    )
    weight: float = Field(
        ..., gt=0.0, le=1.0,
        description="Component weight; weights are normalized if they do not sum to 1.0.",
    )
    nist_function: Optional[NISTFunction] = Field(
        None,
        description="Optional NIST AI RMF function this component maps to.",
    )


class ReliabilityScoreInput(BaseModel):
    """Request body for POST /reliability/score."""

    system_name: str = Field(..., min_length=1, max_length=200)
    components: List[ReliabilityScoreComponent] = Field(..., min_length=1)


class NISTBreakdown(BaseModel):
    """Per-function weighted-average score, 0-100. None if no components
    in the request were tagged for that function."""

    govern: Optional[float] = None
    map: Optional[float] = None
    measure: Optional[float] = None
    manage: Optional[float] = None


class ReliabilityScoreOutput(BaseModel):
    """Response body for POST /reliability/score."""

    system_name: str
    composite_score: float = Field(..., description="Weighted composite score, 0-100.")
    tier: str = Field(..., description="LOW (>=80), MEDIUM (>=60), or HIGH (<60).")
    weights_normalized: bool = Field(
        ...,
        description="True if input weights did not sum to 1.0 and were normalized.",
    )
    nist_breakdown: NISTBreakdown
    components: List[ReliabilityScoreComponent]
    computed_at: datetime


# ---------- Reliability Score Explanation (Sprint 2, E2-S2) ----------

class ScoreContribution(BaseModel):
    """One component's contribution to the composite score."""

    component_name: str
    value: float
    weight: float
    contribution: float = Field(
        ...,
        description="Component's share of the composite score on a 0-100 scale "
                    "(normalized weight * value * 100).",
    )
    contribution_percent: float = Field(
        ...,
        description="Percent of the composite score attributable to this component "
                    "(sums to 100 across all components when composite > 0).",
    )
    nist_function: Optional[NISTFunction] = None


class TierGap(BaseModel):
    """How close the current composite is to adjacent tiers."""

    current_tier: str
    next_tier_up: Optional[str] = Field(
        None,
        description="Tier label above the current one, or null if already at LOW.",
    )
    points_needed_up: Optional[float] = Field(
        None,
        description="Composite points needed to jump to the next tier up.",
    )
    next_tier_down: Optional[str] = Field(
        None,
        description="Tier label below the current one, or null if already at HIGH.",
    )
    points_buffer_down: Optional[float] = Field(
        None,
        description="Composite points of headroom before falling to the next tier down.",
    )


class ScoreExplanation(BaseModel):
    """Human- and machine-readable rationale for a composite score."""

    top_driver: Optional[ScoreContribution] = Field(
        None,
        description="Component contributing most to the composite score.",
    )
    top_gap: Optional[ScoreContribution] = Field(
        None,
        description="Component with the lowest value (largest improvement opportunity).",
    )
    contributions: List[ScoreContribution] = Field(
        ...,
        description="Per-component contributions, sorted highest first.",
    )
    tier_gap: TierGap
    weakest_nist_function: Optional[NISTFunction] = None
    strongest_nist_function: Optional[NISTFunction] = None
    recommendation: str = Field(
        ...,
        description="One-sentence plain-English suggestion for the owner.",
    )


class ReliabilityScoreWithExplanation(ReliabilityScoreOutput):
    """Response body for POST /reliability/score/explain.

    Extends the base score response with a detailed ``explanation`` object
    that tells the caller *why* the composite landed where it did and what
    to do about it.
    """

    explanation: ScoreExplanation


# ---------- Reliability Score History (Sprint 2, E2-S3) ----------

class ReliabilityScoreRecordOut(BaseModel):
    """One persisted reliability score row."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    system_name: str
    composite_score: float
    tier: str
    weights_normalized: bool
    nist_govern: Optional[float] = None
    nist_map: Optional[float] = None
    nist_measure: Optional[float] = None
    nist_manage: Optional[float] = None
    created_at: datetime


class TierTransition(BaseModel):
    """One tier change detected in the history stream."""

    from_tier: str
    to_tier: str
    at: datetime
    composite_score: float = Field(
        ...,
        description="Composite score at the moment of the transition.",
    )


class ScoreTrendStats(BaseModel):
    """Aggregate statistics computed across a history window."""

    count: int
    latest_score: Optional[float] = None
    latest_tier: Optional[str] = None
    earliest_score: Optional[float] = None
    earliest_tier: Optional[str] = None
    rolling_average: Optional[float] = Field(
        None,
        description="Mean composite score across all returned records.",
    )
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    trend_direction: str = Field(
        ...,
        description="'improving', 'degrading', 'stable', or 'insufficient_data'.",
    )
    tier_transitions: List[TierTransition] = Field(default_factory=list)


class ReliabilityScoreHistoryOut(BaseModel):
    """Response body for GET /reliability/score/history."""

    system_name: Optional[str] = Field(
        None,
        description="Filter applied (``None`` = all systems).",
    )
    stats: ScoreTrendStats
    records: List[ReliabilityScoreRecordOut]


# ---------- Policy Gate (Sprint 3, E3-S1) ----------

class PolicyDecision(str, Enum):
    """Overall gate outcome."""

    allow = "allow"
    warn = "warn"
    block = "block"


class PolicySeverity(str, Enum):
    """Severity classification for a single policy reason."""

    info = "info"
    warn = "warn"
    block = "block"


class PolicyThresholds(BaseModel):
    """Configurable thresholds controlling the gate outcome.

    ``allow_min_composite`` and ``warn_min_composite`` partition the
    composite score into allow / warn / block bands; ``min_nist_function_score``
    is a hard floor -- any per-NIST-function breakdown below it forces
    ``block`` regardless of composite.
    """

    allow_min_composite: float = Field(
        80.0, ge=0.0, le=100.0,
        description="Composite score >= this value maps to 'allow'.",
    )
    warn_min_composite: float = Field(
        60.0, ge=0.0, le=100.0,
        description="Composite score >= this (and < allow threshold) maps to 'warn'.",
    )
    min_nist_function_score: float = Field(
        40.0, ge=0.0, le=100.0,
        description="Per-function score floor; any tagged NIST function below "
                    "this value forces 'block'.",
    )

    @field_validator("warn_min_composite")
    @classmethod
    def _warn_below_allow(cls, v: float, info) -> float:
        allow_min = info.data.get("allow_min_composite", 80.0)
        if v > allow_min:
            raise ValueError(
                "warn_min_composite must be <= allow_min_composite"
            )
        return v


class PolicyReason(BaseModel):
    """One machine-readable + human-readable rationale for the decision."""

    code: str = Field(..., description="Short stable identifier for the rule.")
    message: str = Field(..., description="Plain-English explanation.")
    severity: PolicySeverity


class PolicyGateInput(BaseModel):
    """Request body for POST /policy/evaluate."""

    score_input: ReliabilityScoreInput
    thresholds: Optional[PolicyThresholds] = Field(
        None,
        description="Override the default thresholds; omit to use defaults.",
    )


class PolicyGateDecision(BaseModel):
    """Response body for POST /policy/evaluate."""

    system_name: str
    decision: PolicyDecision
    composite_score: float
    tier: str
    reasons: List[PolicyReason] = Field(
        ...,
        description="All rules that fired, worst severity first.",
    )
    thresholds_applied: PolicyThresholds
    evaluated_at: datetime


# ---------- Policy Audit Log (Sprint 3, E3-S3) ----------

class PolicyEvaluationRecordOut(BaseModel):
    """One persisted ``POST /policy/evaluate`` row."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    system_name: str
    decision: PolicyDecision
    composite_score: float
    tier: str
    thresholds: PolicyThresholds
    reasons: List[PolicyReason] = Field(default_factory=list)
    created_at: datetime


class PolicyDecisionTransition(BaseModel):
    """One decision change detected in the history stream.

    Mirrors :class:`TierTransition` but for gate outcomes; shows when a
    system crossed from one ``allow`` / ``warn`` / ``block`` state to
    another.
    """

    from_decision: PolicyDecision
    to_decision: PolicyDecision
    at: datetime
    composite_score: float = Field(
        ...,
        description="Composite score at the moment of the transition.",
    )


class PolicyTrendStats(BaseModel):
    """Aggregate statistics computed across a policy-history window."""

    count: int
    latest_decision: Optional[PolicyDecision] = None
    latest_composite: Optional[float] = None
    earliest_decision: Optional[PolicyDecision] = None
    earliest_composite: Optional[float] = None
    allow_count: int = 0
    warn_count: int = 0
    block_count: int = 0
    allow_rate: Optional[float] = Field(
        None,
        description="allow_count / count, 0-1.",
    )
    warn_rate: Optional[float] = Field(
        None,
        description="warn_count / count, 0-1.",
    )
    block_rate: Optional[float] = Field(
        None,
        description="block_count / count, 0-1.",
    )
    rolling_average_composite: Optional[float] = Field(
        None,
        description="Mean composite score across all returned records.",
    )
    min_composite: Optional[float] = None
    max_composite: Optional[float] = None
    trend_direction: str = Field(
        ...,
        description="'improving', 'degrading', 'stable', or 'insufficient_data' "
                    "(based on composite score, matching /reliability/score/history).",
    )
    decision_transitions: List[PolicyDecisionTransition] = Field(
        default_factory=list,
        description="Every place the decision changed, chronological.",
    )


class PolicyHistoryOut(BaseModel):
    """Response body for GET /policy/history."""

    system_name: Optional[str] = Field(
        None,
        description="Filter applied (``None`` = all systems).",
    )
    stats: PolicyTrendStats
    records: List[PolicyEvaluationRecordOut]


# ---------- Audit Ledger (Sprint 5, E5-S2 local slice) ----------

class AuditLogRecordOut(BaseModel):
    """One persisted append-only audit ledger row."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: str
    entity_type: str
    entity_key: Optional[str] = None
    actor_email: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    previous_hash: Optional[str] = None
    record_hash: str
    created_at: datetime


class AuditLogStats(BaseModel):
    """Aggregate facts about the returned audit-history window."""

    count: int
    latest_hash: Optional[str] = None
    oldest_hash: Optional[str] = None


class AuditLogHistoryOut(BaseModel):
    """Response body for GET /audit/history."""

    event_type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_key: Optional[str] = None
    stats: AuditLogStats
    records: List[AuditLogRecordOut] = Field(default_factory=list)


class AuditChainIssueOut(BaseModel):
    """One audit-chain verification failure."""

    record_id: int
    issue: str
    expected: Optional[str] = None
    actual: Optional[str] = None


class AuditChainVerificationOut(BaseModel):
    """Response body for GET /audit/verify."""

    chain_valid: bool
    checked_records: int
    latest_hash: Optional[str] = None
    issues: List[AuditChainIssueOut] = Field(default_factory=list)


# ---------- Retention and Legal Hold (Sprint 5, E5-S3 local slice) ----------

class RetentionPolicyInput(BaseModel):
    retention_days: int = Field(
        ...,
        ge=0,
        le=36500,
        description="Days before an audit record becomes eligible for review. "
                    "0 is allowed for local validation.",
    )
    notes: Optional[str] = Field(default=None, max_length=2000)


class RetentionPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    retention_days: int
    configured_by_email: str
    notes: Optional[str] = None
    created_at: datetime


class LegalHoldInput(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_key: str = Field(..., min_length=1, max_length=200)
    reason: str = Field(..., min_length=1, max_length=2000)


class LegalHoldReleaseInput(BaseModel):
    release_notes: Optional[str] = Field(default=None, max_length=2000)


class LegalHoldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_key: str
    reason: str
    active: bool
    created_by_email: str
    released_by_email: Optional[str] = None
    release_notes: Optional[str] = None
    created_at: datetime
    released_at: Optional[datetime] = None


class RetentionStatusOut(BaseModel):
    generated_at: datetime
    retention_days: int
    total_audit_records: int
    active_legal_holds: int
    held_record_count: int
    eligible_record_count: int
    held_record_ids: List[int] = Field(default_factory=list)
    eligible_record_ids: List[int] = Field(default_factory=list)


# ---------- Dashboard / Reporting (Sprint 4 + Sprint 5 slice) ----------

class DashboardEpic(BaseModel):
    """One backlog epic exposed to the dashboard."""

    id: str
    title: str
    status: str
    sprint: int


class DashboardMetric(BaseModel):
    """Small KPI card used by the dashboard and executive export."""

    key: str
    label: str
    value: str
    target: Optional[str] = None
    status: str = Field(
        ...,
        description="'good', 'attention', 'blocked', or 'empty'.",
    )
    detail: str


class AssessmentSummaryOut(BaseModel):
    """Aggregate counts across stored assessments."""

    total: int = 0
    low_risk: int = 0
    medium_risk: int = 0
    high_risk: int = 0
    allow_count: int = 0
    warn_count: int = 0
    block_count: int = 0


class ComplianceControlOut(BaseModel):
    """One control row in the security/compliance evidence bundle."""

    control_id: str
    title: str
    status: str = Field(
        ...,
        description="'implemented', 'partial', 'planned', or 'blocked'.",
    )
    summary: str
    evidence: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


class ComplianceEvidenceBundleOut(BaseModel):
    """Security/compliance evidence bundle assembled from repo-backed facts."""

    generated_at: datetime
    overall_status: str
    controls: List[ComplianceControlOut] = Field(default_factory=list)
    outstanding_gaps: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)


class DashboardSummaryOut(BaseModel):
    """Role-aware dashboard summary for the Sprint 4 web UI."""

    generated_at: datetime
    viewer_role: str
    release: str
    branch: str
    current_sprint: int
    total_sprints: int
    epics: List[DashboardEpic] = Field(default_factory=list)
    epic_completion_percent: float = 0.0
    metrics: List[DashboardMetric] = Field(default_factory=list)
    assessment_summary: AssessmentSummaryOut
    recent_assessments: List["AssessmentOutput"] = Field(default_factory=list)
    score_history: ReliabilityScoreHistoryOut
    policy_history: PolicyHistoryOut


class ExecutiveSummaryOut(BaseModel):
    """Unified executive summary used by the JSON and PDF exports."""

    generated_at: datetime
    viewer_role: str
    release: str
    branch: str
    current_sprint: int
    total_sprints: int
    dashboard: DashboardSummaryOut
    compliance: ComplianceEvidenceBundleOut


# ---------- Hash ----------

class HashInput(BaseModel):
    text: str


class HashOutput(BaseModel):
    text: str
    sha256: str
    length: int


# ---------- Assessments (NIST AI RMF) ----------

class AssessmentInput(BaseModel):
    system_name: str = Field(..., min_length=1, max_length=200)
    owner: str = Field(..., min_length=1, max_length=200)
    govern_score: int = Field(..., ge=0, le=100)
    map_score: int = Field(..., ge=0, le=100)
    measure_score: int = Field(..., ge=0, le=100)
    manage_score: int = Field(..., ge=0, le=100)
    notes: Optional[str] = None


class AssessmentOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    system_name: str
    owner: str
    govern_score: int
    map_score: int
    measure_score: int
    manage_score: int
    overall_score: float
    risk_tier: str
    notes: Optional[str] = None
    created_at: datetime
    # Sprint 3, E3-S2: every assessment now carries the policy-gate decision
    # computed against its own scores so the UI / audit log never have to
    # re-run the gate to find out whether it should have shipped.
    gate_decision: Optional[PolicyDecision] = Field(
        None,
        description="Policy gate outcome computed at creation time "
                    "(null for pre-E3-S2 rows).",
    )
    gate_reasons: List[PolicyReason] = Field(
        default_factory=list,
        description="Gate reasons that fired, worst-severity first.",
    )


# ---------- AI / ML ----------

class AnomalyInput(BaseModel):
    records: List[List[float]] = Field(
        ...,
        min_length=2,
        description="List of feature vectors (2+ records required)",
    )
    contamination: float = Field(0.1, gt=0, lt=0.5)


class AnomalyOutput(BaseModel):
    n_trained_on: int
    n_scored: int
    predictions: List[int]
    scores: List[float]
    anomaly_count: int
    model: str
    record_ids: Optional[List[int]] = None
