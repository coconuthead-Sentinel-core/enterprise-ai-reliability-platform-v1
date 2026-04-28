"""
Pydantic data models for the Enterprise AI Reliability Platform (EARP).

Covers all core entities: LLMModelVersion, PromptSetVersion, LLMEvaluationRun,
GateDecision, and all API request/response schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
import uuid


# ---------------------------------------------------------------------------
# Core entity models
# ---------------------------------------------------------------------------

class LLMModelVersion(BaseModel):
    """Represents a versioned LLM artifact under evaluation."""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    model_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str = Field(..., description="LLM provider name (e.g. OpenAI, Anthropic)")
    model_name: str = Field(..., description="Human-readable model name")
    model_version: str = Field(..., description="Semantic version string")
    release_date: Optional[datetime] = Field(
        default=None, description="Intended release date for this model version"
    )


class PromptSetVersion(BaseModel):
    """Represents a versioned benchmark prompt set used in evaluation."""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    prompt_set_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt_set_version: str = Field(..., description="Version of the prompt set")
    benchmark_suite_id: str = Field(..., description="Parent benchmark suite identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LLMEvaluationRun(BaseModel):
    """
    Represents a single evaluation run of an LLM model version against a prompt set.

    Contains both raw metric counts and pre-computed constraint inputs used
    by the PolicyEvaluationService.
    """

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    evaluation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_id: str = Field(..., description="Reference to LLMModelVersion.model_id")
    model_version: str = Field(..., description="Model version string evaluated")
    prompt_set_id: str = Field(..., description="Reference to PromptSetVersion.prompt_set_id")
    prompt_set_version: str = Field(..., description="Prompt set version used")

    # Raw metric counts
    total_prompts: int = Field(..., ge=1, description="Total prompts in the evaluation run")
    successful_tasks: int = Field(..., ge=0, description="Number of tasks completed successfully")
    supported_claims: int = Field(..., ge=0, description="Number of grounded/supported claims")
    unsupported_claims: int = Field(..., ge=0, description="Number of unsupported/hallucinated claims")
    policy_violations: int = Field(..., ge=0, description="Number of safety/policy violations")
    p95_latency_ms: float = Field(..., ge=0, description="95th percentile latency in milliseconds")
    total_inference_cost_usd: float = Field(..., ge=0, description="Total inference cost in USD")

    # Adversarial robustness metrics
    adversarial_tests_passed: int = Field(..., ge=0, description="Adversarial tests passed")
    adversarial_tests_total: int = Field(..., ge=1, description="Total adversarial tests run")

    # Hard constraint inputs (explicit, to allow override from external validation pipelines)
    hallucination_rate: Optional[float] = Field(
        default=None,
        description=(
            "Override hallucination rate. If None, computed as "
            "unsupported_claims / (supported_claims + unsupported_claims)."
        ),
    )
    safety_violation_rate: Optional[float] = Field(
        default=None,
        description=(
            "Override safety violation rate. If None, computed as "
            "policy_violations / total_prompts."
        ),
    )
    critical_vuln_count: int = Field(
        default=0, ge=0, description="Critical vulnerability count from security scan"
    )
    compliance_artifacts_complete: bool = Field(
        default=True, description="Whether all required legal/compliance artifacts are present"
    )

    # SLO and audit metadata
    latency_slo_ms: float = Field(
        default=2500.0, description="SLO threshold for p95 latency in ms"
    )
    audit_completeness_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Fraction of required audit artifacts that are complete (0.0-1.0)",
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)


class GateDecision(BaseModel):
    """Represents an immutable gate decision produced by PolicyEvaluationService."""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evaluation_id: str = Field(..., description="Reference to LLMEvaluationRun.evaluation_id")
    policy_score: float = Field(..., ge=0.0, le=1.0, description="Weighted policy score (0-1)")
    result: str = Field(..., description="One of: pass | conditional | fail")
    rationale: str = Field(..., description="Human-readable rationale for the decision")
    decided_at: datetime = Field(default_factory=datetime.utcnow)

    # Sub-scores included for transparency
    groundedness_score: float = Field(..., ge=0.0, le=1.0)
    task_success_rate: float = Field(..., ge=0.0, le=1.0)
    prompt_robustness: float = Field(..., ge=0.0, le=1.0)
    safety_compliance_score: float = Field(..., ge=0.0, le=1.0)
    latency_slo_compliance: float = Field(..., ge=0.0, le=1.0)
    audit_completeness: float = Field(..., ge=0.0, le=1.0)

    # Hard constraint results
    hallucination_rate_actual: float = Field(..., description="Actual hallucination rate evaluated")
    safety_violation_rate_actual: float = Field(..., description="Actual safety violation rate evaluated")
    hard_constraints_passed: bool = Field(..., description="Whether all hard constraints passed")


# ---------------------------------------------------------------------------
# API request / response schemas
# ---------------------------------------------------------------------------

class EvaluationRequest(BaseModel):
    """
    Payload submitted to POST /api/v1/evaluations.

    Wraps an LLMEvaluationRun with connector metadata fields for
    ConnectorGateway validation.
    """

    # ConnectorGateway metadata (10-field YAML schema)
    node_id: str = Field(..., description="Unique node identifier in the evidence graph")
    node_type: str = Field(..., description="Type of evidence node (e.g. evaluation_run)")
    title: str = Field(..., description="Human-readable title for this evidence payload")
    owner_role: str = Field(..., description="Role of the submitting owner")
    source_system: str = Field(..., description="Source system that produced the evaluation")
    created_utc: str = Field(..., description="ISO-8601 UTC creation timestamp")
    updated_utc: str = Field(..., description="ISO-8601 UTC last-update timestamp")
    zone_state: str = Field(..., description="Zone state of the evidence node")
    entropy_state: str = Field(..., description="Entropy state of the evidence node")
    anchor_ref: str = Field(..., description="Reference anchor for lineage tracking")

    # Core evaluation data
    evaluation: LLMEvaluationRun


class GateDecisionResponse(BaseModel):
    """Response envelope returned by POST /api/v1/evaluations/{id}/gate."""

    evaluation_id: str
    decision: GateDecision
    kpi_summary: Dict[str, Any] = Field(
        default_factory=dict, description="KPI values computed from this evaluation run"
    )


class KPIReport(BaseModel):
    """
    KPI dashboard report returned by GET /api/v1/kpis.

    Aggregates all 7 KPIs across all registered evaluation runs.
    """

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_count: int = Field(..., description="Number of evaluation runs included")

    # KPI-1: Groundedness
    kpi_1_groundedness_score: float = Field(..., description="Avg groundedness (target >= 0.92)")
    kpi_1_target: float = Field(default=0.92)
    kpi_1_pass: bool

    # KPI-2: Hallucination Rate
    kpi_2_hallucination_rate: float = Field(..., description="Avg hallucination rate (target <= 0.03)")
    kpi_2_target: float = Field(default=0.03)
    kpi_2_pass: bool

    # KPI-3: Task Success Rate
    kpi_3_task_success_rate: float = Field(..., description="Avg task success rate (target >= 0.90)")
    kpi_3_target: float = Field(default=0.90)
    kpi_3_pass: bool

    # KPI-4: Safety Violation Rate
    kpi_4_safety_violation_rate: float = Field(
        ..., description="Avg safety violation rate (target <= 0.01)"
    )
    kpi_4_target: float = Field(default=0.01)
    kpi_4_pass: bool

    # KPI-5: P95 Latency
    kpi_5_p95_latency_ms: float = Field(..., description="Avg P95 latency ms (target <= 2500)")
    kpi_5_target_ms: float = Field(default=2500.0)
    kpi_5_pass: bool

    # KPI-6: Cost Per Successful Task
    kpi_6_cost_per_successful_task_usd: float = Field(
        ..., description="Avg cost per successful task in USD"
    )
    kpi_6_target: Optional[float] = Field(default=None, description="No fixed target defined")

    # KPI-7: Gate Pass Rate
    kpi_7_gate_pass_rate: float = Field(..., description="Gate pass rate (target >= 0.80)")
    kpi_7_target: float = Field(default=0.80)
    kpi_7_pass: bool


class AuditReport(BaseModel):
    """Immutable audit report produced by AuditReportingService."""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evaluation_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_snapshot: Dict[str, Any] = Field(..., description="Snapshot of the evaluation run")
    decision_trail: List[Dict[str, Any]] = Field(
        default_factory=list, description="Ordered list of all gate decisions for this evaluation"
    )
    evidence_references: List[str] = Field(
        default_factory=list, description="Lineage references from EvidenceRegistryService"
    )
    connector_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Original connector-gateway metadata"
    )
    immutability_hash: str = Field(..., description="SHA-256 hash of report contents for integrity")
