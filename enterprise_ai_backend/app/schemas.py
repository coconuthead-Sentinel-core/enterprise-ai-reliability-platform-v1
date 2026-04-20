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
