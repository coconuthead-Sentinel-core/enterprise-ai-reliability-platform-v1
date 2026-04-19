import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "libs"))

from policy.scoring import compute_metrics, compute_reliability_index, LATENCY_THRESHOLD_MS


def test_perfect_run_scores_one():
    metrics = compute_metrics(
        total_prompts=100, successful_tasks=100,
        supported_claims=100, unsupported_claims=0,
        policy_violations=0, p95_latency_ms=500,
        prompt_robustness=1.0, availability=1.0,
    )
    score = compute_reliability_index(metrics)
    assert score == 1.0


def test_zero_claims_groundedness_defaults_to_one():
    metrics = compute_metrics(
        total_prompts=10, successful_tasks=10,
        supported_claims=0, unsupported_claims=0,
        policy_violations=0, p95_latency_ms=500,
    )
    assert metrics.groundedness == 1.0


def test_latency_above_threshold_yields_zero_compliance():
    metrics = compute_metrics(
        total_prompts=10, successful_tasks=10,
        supported_claims=10, unsupported_claims=0,
        policy_violations=0, p95_latency_ms=LATENCY_THRESHOLD_MS + 1,
    )
    assert metrics.latency_compliance == 0.0


def test_latency_at_threshold_yields_full_compliance():
    metrics = compute_metrics(
        total_prompts=10, successful_tasks=10,
        supported_claims=10, unsupported_claims=0,
        policy_violations=0, p95_latency_ms=LATENCY_THRESHOLD_MS,
    )
    assert metrics.latency_compliance == 1.0


def test_reliability_index_weights_sum_to_one():
    # All inputs at 1 should produce 1.0
    metrics = compute_metrics(
        total_prompts=1, successful_tasks=1,
        supported_claims=1, unsupported_claims=0,
        policy_violations=0, p95_latency_ms=100,
        prompt_robustness=1.0, availability=1.0,
    )
    score = compute_reliability_index(metrics)
    assert abs(score - 1.0) < 1e-9


def test_all_violations_lowers_score():
    metrics = compute_metrics(
        total_prompts=10, successful_tasks=0,
        supported_claims=0, unsupported_claims=10,
        policy_violations=10, p95_latency_ms=9999,
        prompt_robustness=0.0, availability=0.0,
    )
    score = compute_reliability_index(metrics)
    assert score == 0.0
