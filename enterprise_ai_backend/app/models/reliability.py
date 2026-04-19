"""Pydantic models for the Reliability Scoring Engine.

Field names follow the OpenAPI spec (camelCase) with snake_case aliases
so Python code stays idiomatic while JSON payloads match the contract.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class ReliabilityScoreRequest(BaseModel):
    """Input metrics for a single reliability evaluation.

    All counts must be non-negative.  The request mirrors the fields
    defined in ``EvaluationRunCreate`` from the OpenAPI spec plus the
    additional subscore inputs required by the Readiness Policy Spec §1-2.
    """

    # Core evaluation counts (from EvaluationRunCreate)
    total_prompts: int = Field(..., ge=1, description="Total prompts evaluated")
    successful_tasks: int = Field(..., ge=0, description="Tasks completed successfully")
    supported_claims: int = Field(..., ge=0, description="Claims with supporting evidence")
    unsupported_claims: int = Field(..., ge=0, description="Claims without supporting evidence")
    policy_violations: int = Field(..., ge=0, description="Safety / policy violation count")
    p95_latency_ms: float = Field(..., ge=0, description="P95 latency in milliseconds")
    total_inference_cost_usd: float = Field(
        ..., ge=0, description="Total inference cost in USD"
    )

    # SLO / compliance inputs (from Readiness Policy Spec §2)
    latency_slo_ms: float = Field(
        default=2500.0, ge=0, description="Latency SLO threshold in milliseconds"
    )
    total_requests: int = Field(
        default=0, ge=0, description="Total requests for latency SLO compliance"
    )
    compliant_requests: int = Field(
        default=0, ge=0, description="Requests meeting latency SLO"
    )

    # Prompt robustness (adversarial testing)
    adversarial_tests_total: int = Field(
        default=0, ge=0, description="Total adversarial tests run"
    )
    adversarial_tests_passed: int = Field(
        default=0, ge=0, description="Adversarial tests passed"
    )

    # Audit completeness
    required_artifacts: int = Field(
        default=0, ge=0, description="Required audit artifacts"
    )
    complete_artifacts: int = Field(
        default=0, ge=0, description="Audit artifacts completed"
    )

    # Availability (for SDLC ReliabilityIndex)
    availability: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Service availability ratio (0-1)"
    )


# ---------------------------------------------------------------------------
# Sub-score detail
# ---------------------------------------------------------------------------


class SubScores(BaseModel):
    """Intermediate metrics derived from the raw counts."""

    groundedness_score: float = Field(..., description="supported / total claims")
    task_success_rate: float = Field(..., description="successful / total tasks")
    hallucination_rate: float = Field(..., description="unsupported / total claims")
    safety_violation_rate: float = Field(..., description="violations / total evaluations")
    prompt_robustness: float = Field(..., description="adversarial passed / total")
    latency_slo_compliance: float = Field(..., description="compliant / total requests")
    audit_completeness: float = Field(..., description="complete / required artifacts")
    cost_per_successful_task: float | None = Field(
        None, description="cost / successful tasks (null if 0 successes)"
    )
    availability: float = Field(..., description="Service availability ratio")


# ---------------------------------------------------------------------------
# Gate outcome
# ---------------------------------------------------------------------------


class GateResult(str, Enum):
    """Release-gate outcome per Readiness Policy Spec §3."""

    PASS = "pass"
    CONDITIONAL = "conditional"
    FAIL = "fail"


# ---------------------------------------------------------------------------
# Hard-constraint violations
# ---------------------------------------------------------------------------


class HardConstraintViolation(BaseModel):
    """A single hard-constraint that was not met."""

    constraint: str
    threshold: str
    actual: str


# ---------------------------------------------------------------------------
# NIST AI RMF mapping
# ---------------------------------------------------------------------------


class NistRmfMapping(BaseModel):
    """Maps the score to NIST AI RMF 1.0 functions."""

    govern: str = Field(
        ..., description="Govern function: role responsibilities and accountability"
    )
    map: str = Field(
        ..., description="Map function: context, use case, and impact boundaries"
    )
    measure: str = Field(
        ..., description="Measure function: risk metrics and validation methods"
    )
    manage: str = Field(
        ..., description="Manage function: treatment plans and escalation protocols"
    )


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class ReliabilityScoreResponse(BaseModel):
    """Full response from POST /reliability/score."""

    reliability_index: float = Field(
        ..., description="SDLC composite reliability index (0-1)"
    )
    policy_score: float = Field(
        ..., description="Release-gate composite policy score (0-1)"
    )
    gate_result: GateResult = Field(
        ..., description="Release-gate outcome"
    )
    rationale: str = Field(
        ..., description="Human-readable explanation of the gate decision"
    )
    sub_scores: SubScores
    hard_constraint_violations: list[HardConstraintViolation] = Field(
        default_factory=list,
        description="List of hard-constraint violations (empty when all pass)",
    )
    nist_rmf: NistRmfMapping
