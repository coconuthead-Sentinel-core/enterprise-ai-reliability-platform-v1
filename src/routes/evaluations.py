"""
API route handlers for the EARP evaluations resource.

Routes:
    POST   /api/v1/evaluations                            — submit evaluation run
    GET    /api/v1/evaluations/{evaluation_id}            — retrieve evaluation run
    POST   /api/v1/evaluations/{evaluation_id}/gate       — trigger gate decision
    GET    /api/v1/evaluations/{evaluation_id}/audit      — get audit report
    GET    /api/v1/kpis                                   — KPI dashboard
    GET    /api/v1/health                                 — health check
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends

from src.models import (
    EvaluationRequest,
    LLMEvaluationRun,
    GateDecision,
    GateDecisionResponse,
    KPIReport,
    AuditReport,
)
from src.services.connector_service import ConnectorGateway, ConnectorValidationError
from src.services.evidence_service import EvidenceRegistryService
from src.services.scoring_service import ReliabilityScoringService
from src.services.policy_service import PolicyEvaluationService
from src.services.audit_service import AuditReportingService

router = APIRouter(prefix="/api/v1", tags=["evaluations"])

# ---------------------------------------------------------------------------
# Service singletons — injected via FastAPI dependency overrides in main.py.
# Default instances are used when no override is provided (e.g. in tests).
# ---------------------------------------------------------------------------

_connector = ConnectorGateway()
_evidence = EvidenceRegistryService()
_scoring = ReliabilityScoringService()
_policy = PolicyEvaluationService()
_audit = AuditReportingService()

# In-memory gate decision store: evaluation_id -> list of GateDecision
_decisions: Dict[str, List[GateDecision]] = {}


def get_connector() -> ConnectorGateway:
    """Dependency: return the ConnectorGateway singleton."""
    return _connector


def get_evidence() -> EvidenceRegistryService:
    """Dependency: return the EvidenceRegistryService singleton."""
    return _evidence


def get_policy() -> PolicyEvaluationService:
    """Dependency: return the PolicyEvaluationService singleton."""
    return _policy


def get_audit() -> AuditReportingService:
    """Dependency: return the AuditReportingService singleton."""
    return _audit


# ---------------------------------------------------------------------------
# Route: POST /api/v1/evaluations
# ---------------------------------------------------------------------------

@router.post(
    "/evaluations",
    response_model=LLMEvaluationRun,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new evaluation run",
    description=(
        "Validates the incoming payload via ConnectorGateway and registers the "
        "evaluation run in EvidenceRegistryService with full lineage tracking."
    ),
)
def submit_evaluation(
    request: EvaluationRequest,
    connector: ConnectorGateway = Depends(get_connector),
    evidence: EvidenceRegistryService = Depends(get_evidence),
) -> LLMEvaluationRun:
    """Submit a new LLM evaluation run for registration."""
    # Build the connector metadata dict for validation
    metadata = {
        "node_id": request.node_id,
        "node_type": request.node_type,
        "title": request.title,
        "owner_role": request.owner_role,
        "source_system": request.source_system,
        "created_utc": request.created_utc,
        "updated_utc": request.updated_utc,
        "zone_state": request.zone_state,
        "entropy_state": request.entropy_state,
        "anchor_ref": request.anchor_ref,
    }

    # Validate via ConnectorGateway
    try:
        connector.validate_or_raise(metadata)
    except ConnectorValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "ConnectorGateway validation failed", "errors": exc.errors},
        )

    # Register in EvidenceRegistryService with lineage
    run = evidence.register(request.evaluation, connector_metadata=metadata)
    return run


# ---------------------------------------------------------------------------
# Route: GET /api/v1/evaluations/{evaluation_id}
# ---------------------------------------------------------------------------

@router.get(
    "/evaluations/{evaluation_id}",
    response_model=LLMEvaluationRun,
    summary="Retrieve an evaluation run by ID",
)
def get_evaluation(
    evaluation_id: str,
    evidence: EvidenceRegistryService = Depends(get_evidence),
) -> LLMEvaluationRun:
    """Retrieve a registered evaluation run by its unique ID."""
    run = evidence.get(evaluation_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{evaluation_id}' not found.",
        )
    return run


# ---------------------------------------------------------------------------
# Route: POST /api/v1/evaluations/{evaluation_id}/gate
# ---------------------------------------------------------------------------

@router.post(
    "/evaluations/{evaluation_id}/gate",
    response_model=GateDecisionResponse,
    summary="Trigger a gate decision for an evaluation run",
    description=(
        "Runs the full scoring and policy evaluation pipeline and returns a "
        "PASS / CONDITIONAL / FAIL decision with rationale and KPI summary."
    ),
)
def trigger_gate(
    evaluation_id: str,
    evidence: EvidenceRegistryService = Depends(get_evidence),
    policy: PolicyEvaluationService = Depends(get_policy),
) -> GateDecisionResponse:
    """Trigger gate evaluation for a registered evaluation run."""
    run = evidence.get(evaluation_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{evaluation_id}' not found.",
        )

    # Run gate evaluation
    decision = policy.evaluate(run)

    # Store the decision
    if evaluation_id not in _decisions:
        _decisions[evaluation_id] = []
    _decisions[evaluation_id].append(decision)

    # Compute KPI summary for this run
    scorer = ReliabilityScoringService()
    scores = scorer.compute_policy_score(run)
    total_claims = run.supported_claims + run.unsupported_claims

    kpi_summary = {
        "kpi_1_groundedness": scores["groundedness_score"],
        "kpi_2_hallucination_rate": scores["hallucination_rate"],
        "kpi_3_task_success_rate": scores["task_success_rate"],
        "kpi_4_safety_violation_rate": scores["safety_violation_rate"],
        "kpi_5_p95_latency_ms": run.p95_latency_ms,
        "kpi_6_cost_per_successful_task_usd": (
            round(run.total_inference_cost_usd / run.successful_tasks, 6)
            if run.successful_tasks > 0
            else None
        ),
        "kpi_7_gate_result": decision.result,
    }

    return GateDecisionResponse(
        evaluation_id=evaluation_id,
        decision=decision,
        kpi_summary=kpi_summary,
    )


# ---------------------------------------------------------------------------
# Route: GET /api/v1/evaluations/{evaluation_id}/audit
# ---------------------------------------------------------------------------

@router.get(
    "/evaluations/{evaluation_id}/audit",
    response_model=AuditReport,
    summary="Get the immutable audit report for an evaluation run",
)
def get_audit_report(
    evaluation_id: str,
    evidence: EvidenceRegistryService = Depends(get_evidence),
    audit: AuditReportingService = Depends(get_audit),
) -> AuditReport:
    """Generate and return an immutable audit report for an evaluation run."""
    run = evidence.get(evaluation_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{evaluation_id}' not found.",
        )

    decisions = _decisions.get(evaluation_id, [])
    lineage_refs = evidence.get_lineage(evaluation_id)
    connector_metadata = evidence.get_connector_metadata(evaluation_id) or {}

    report = audit.generate_report(
        run=run,
        decisions=decisions,
        lineage_refs=lineage_refs,
        connector_metadata=connector_metadata,
    )
    return report


# ---------------------------------------------------------------------------
# Route: GET /api/v1/kpis
# ---------------------------------------------------------------------------

@router.get(
    "/kpis",
    response_model=KPIReport,
    summary="Get the current KPI dashboard",
    description=(
        "Aggregates all 7 KPIs across all registered evaluation runs. "
        "Returns averages, targets, and pass/fail status for each KPI."
    ),
)
def get_kpis(
    evidence: EvidenceRegistryService = Depends(get_evidence),
) -> KPIReport:
    """Compute and return the KPI dashboard from all registered runs."""
    all_runs = evidence.list_all()

    if not all_runs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No evaluation runs registered. Load mock data or submit evaluations first.",
        )

    scorer = ReliabilityScoringService()
    n = len(all_runs)

    # Accumulators
    total_groundedness = 0.0
    total_hallucination = 0.0
    total_task_success = 0.0
    total_safety_violation = 0.0
    total_p95_latency = 0.0
    total_cost_per_task = 0.0
    gate_decisions_all = []

    for run in all_runs:
        scores = scorer.compute_policy_score(run)
        total_groundedness += scores["groundedness_score"]
        total_hallucination += scores["hallucination_rate"]
        total_task_success += scores["task_success_rate"]
        total_safety_violation += scores["safety_violation_rate"]
        total_p95_latency += run.p95_latency_ms
        if run.successful_tasks > 0:
            total_cost_per_task += run.total_inference_cost_usd / run.successful_tasks

        # Include any gate decisions for this run
        run_decisions = _decisions.get(run.evaluation_id, [])
        gate_decisions_all.extend(run_decisions)

    avg_groundedness = total_groundedness / n
    avg_hallucination = total_hallucination / n
    avg_task_success = total_task_success / n
    avg_safety_violation = total_safety_violation / n
    avg_p95_latency = total_p95_latency / n
    avg_cost_per_task = total_cost_per_task / n

    # KPI-7: Gate pass rate from all recorded decisions
    if gate_decisions_all:
        passed = sum(1 for d in gate_decisions_all if d.result == "pass")
        gate_pass_rate = passed / len(gate_decisions_all)
    else:
        # If no gate decisions yet, compute from mock scores
        gate_pass_rate = 0.0
        for run in all_runs:
            decision = PolicyEvaluationService().evaluate(run)
            if decision.result == "pass":
                gate_pass_rate += 1
        gate_pass_rate = gate_pass_rate / n

    return KPIReport(
        evaluation_count=n,
        kpi_1_groundedness_score=round(avg_groundedness, 6),
        kpi_1_pass=avg_groundedness >= 0.92,
        kpi_2_hallucination_rate=round(avg_hallucination, 6),
        kpi_2_pass=avg_hallucination <= 0.03,
        kpi_3_task_success_rate=round(avg_task_success, 6),
        kpi_3_pass=avg_task_success >= 0.90,
        kpi_4_safety_violation_rate=round(avg_safety_violation, 6),
        kpi_4_pass=avg_safety_violation <= 0.01,
        kpi_5_p95_latency_ms=round(avg_p95_latency, 2),
        kpi_5_pass=avg_p95_latency <= 2500.0,
        kpi_6_cost_per_successful_task_usd=round(avg_cost_per_task, 6),
        kpi_7_gate_pass_rate=round(gate_pass_rate, 6),
        kpi_7_pass=gate_pass_rate >= 0.80,
    )


# ---------------------------------------------------------------------------
# Route: GET /api/v1/health
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    summary="Health check",
    response_model=Dict[str, Any],
)
def health_check(
    evidence: EvidenceRegistryService = Depends(get_evidence),
) -> Dict[str, Any]:
    """Return service health status and basic statistics."""
    return {
        "status": "healthy",
        "service": "Enterprise AI Reliability Platform (EARP)",
        "version": "1.0.0",
        "registered_evaluations": evidence.count(),
        "services": {
            "ConnectorGateway": "operational",
            "EvidenceRegistryService": "operational",
            "ReliabilityScoringService": "operational",
            "PolicyEvaluationService": "operational",
            "AuditReportingService": "operational",
        },
    }
