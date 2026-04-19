from .scoring import compute_metrics, compute_reliability_index, EvaluationMetrics

PASS_THRESHOLD = 0.80
CONDITIONAL_THRESHOLD = 0.60


def evaluate_gate_score(
    metrics: EvaluationMetrics,
    policy_id: str,
) -> tuple[float, str, str]:
    """Returns (score, result, rationale). Deterministic — same inputs always produce same output."""
    score = compute_reliability_index(metrics)

    if score >= PASS_THRESHOLD:
        result = "pass"
        rationale = (
            f"ReliabilityIndex {score:.4f} meets pass threshold {PASS_THRESHOLD} "
            f"(policy={policy_id})."
        )
    elif score >= CONDITIONAL_THRESHOLD:
        result = "conditional"
        rationale = (
            f"ReliabilityIndex {score:.4f} is below pass threshold {PASS_THRESHOLD} "
            f"but meets conditional threshold {CONDITIONAL_THRESHOLD} "
            f"(policy={policy_id})."
        )
    else:
        result = "fail"
        rationale = (
            f"ReliabilityIndex {score:.4f} is below conditional threshold "
            f"{CONDITIONAL_THRESHOLD} (policy={policy_id})."
        )

    return score, result, rationale
