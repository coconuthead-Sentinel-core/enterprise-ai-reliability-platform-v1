from dataclasses import dataclass

# P95 latency threshold from MVP acceptance criteria
LATENCY_THRESHOLD_MS = 2500


@dataclass
class EvaluationMetrics:
    groundedness: float
    task_success: float
    prompt_robustness: float
    safety_violation_rate: float
    latency_compliance: float
    availability: float


def compute_metrics(
    total_prompts: int,
    successful_tasks: int,
    supported_claims: int,
    unsupported_claims: int,
    policy_violations: int,
    p95_latency_ms: int,
    prompt_robustness: float = 1.0,
    availability: float = 1.0,
) -> EvaluationMetrics:
    total_claims = supported_claims + unsupported_claims
    groundedness = supported_claims / total_claims if total_claims > 0 else 1.0
    task_success = successful_tasks / total_prompts if total_prompts > 0 else 0.0
    safety_violation_rate = policy_violations / total_prompts if total_prompts > 0 else 0.0
    latency_compliance = 1.0 if p95_latency_ms <= LATENCY_THRESHOLD_MS else 0.0

    return EvaluationMetrics(
        groundedness=groundedness,
        task_success=task_success,
        prompt_robustness=float(prompt_robustness),
        safety_violation_rate=safety_violation_rate,
        latency_compliance=latency_compliance,
        availability=float(availability),
    )


def compute_reliability_index(metrics: EvaluationMetrics) -> float:
    """
    ReliabilityIndex = 0.30*Groundedness + 0.20*TaskSuccess + 0.15*PromptRobustness
                     + 0.15*(1 - SafetyViolationRate) + 0.10*LatencyCompliance
                     + 0.10*Availability
    Source: architecture_and_api_contracts.txt §4
    """
    return (
        0.30 * metrics.groundedness
        + 0.20 * metrics.task_success
        + 0.15 * metrics.prompt_robustness
        + 0.15 * (1.0 - metrics.safety_violation_rate)
        + 0.10 * metrics.latency_compliance
        + 0.10 * metrics.availability
    )
