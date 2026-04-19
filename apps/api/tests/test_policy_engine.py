import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "libs"))

from policy.scoring import compute_metrics  # noqa: E402
from policy.policy_engine import evaluate_gate_score, PASS_THRESHOLD, CONDITIONAL_THRESHOLD  # noqa: E402


def _perfect_metrics():
    return compute_metrics(
        total_prompts=100, successful_tasks=100,
        supported_claims=100, unsupported_claims=0,
        policy_violations=0, p95_latency_ms=500,
        prompt_robustness=1.0, availability=1.0,
    )


def _failing_metrics():
    return compute_metrics(
        total_prompts=100, successful_tasks=0,
        supported_claims=0, unsupported_claims=100,
        policy_violations=100, p95_latency_ms=9999,
        prompt_robustness=0.0, availability=0.0,
    )


def test_perfect_run_passes():
    score, result, rationale = evaluate_gate_score(_perfect_metrics(), "default-v1")
    assert result == "pass"
    assert score >= PASS_THRESHOLD
    assert "pass" in rationale


def test_failing_run_fails():
    score, result, rationale = evaluate_gate_score(_failing_metrics(), "default-v1")
    assert result == "fail"
    assert score < CONDITIONAL_THRESHOLD


def test_deterministic_same_inputs_same_output():
    m = _perfect_metrics()
    r1 = evaluate_gate_score(m, "p1")
    r2 = evaluate_gate_score(m, "p1")
    assert r1 == r2


def test_policy_id_appears_in_rationale():
    _, _, rationale = evaluate_gate_score(_perfect_metrics(), "my-policy-42")
    assert "my-policy-42" in rationale


def test_conditional_band():
    # Craft a run that scores between 0.60 and 0.80
    metrics = compute_metrics(
        total_prompts=100, successful_tasks=60,
        supported_claims=60, unsupported_claims=40,
        policy_violations=5, p95_latency_ms=3000,
        prompt_robustness=0.7, availability=0.7,
    )
    score, result, _ = evaluate_gate_score(metrics, "p")
    assert CONDITIONAL_THRESHOLD <= score < PASS_THRESHOLD
    assert result == "conditional"
