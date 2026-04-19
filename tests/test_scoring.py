"""Tests for the reliability scoring service.

Covers:
  • Perfect-score pass
  • Minimal-score fail
  • Conditional-pass band
  • Hard-constraint violations (hallucination, safety)
  • Edge cases (zero denominators, boundary values)
  • NIST AI RMF mapping content
  • Sub-score arithmetic
"""

from __future__ import annotations

import pytest

from enterprise_ai_backend.app.models.reliability import (
    GateResult,
    ReliabilityScoreRequest,
)
from enterprise_ai_backend.app.services.scoring import (
    CONDITIONAL_THRESHOLD,
    PASS_THRESHOLD,
    compute_reliability_score,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _perfect_request(**overrides) -> ReliabilityScoreRequest:
    """Return a request that scores perfectly on all metrics."""
    defaults = dict(
        total_prompts=1000,
        successful_tasks=1000,
        supported_claims=980,
        unsupported_claims=0,
        policy_violations=0,
        p95_latency_ms=500.0,
        total_inference_cost_usd=50.0,
        latency_slo_ms=2500.0,
        total_requests=1000,
        compliant_requests=1000,
        adversarial_tests_total=200,
        adversarial_tests_passed=200,
        required_artifacts=10,
        complete_artifacts=10,
        availability=1.0,
    )
    defaults.update(overrides)
    return ReliabilityScoreRequest(**defaults)


def _failing_request(**overrides) -> ReliabilityScoreRequest:
    """Return a request that fails on multiple metrics."""
    defaults = dict(
        total_prompts=100,
        successful_tasks=30,
        supported_claims=50,
        unsupported_claims=50,
        policy_violations=10,
        p95_latency_ms=5000.0,
        total_inference_cost_usd=200.0,
        latency_slo_ms=2500.0,
        total_requests=100,
        compliant_requests=40,
        adversarial_tests_total=50,
        adversarial_tests_passed=20,
        required_artifacts=10,
        complete_artifacts=3,
        availability=0.90,
    )
    defaults.update(overrides)
    return ReliabilityScoreRequest(**defaults)


# ---------------------------------------------------------------------------
# Gate-outcome tests
# ---------------------------------------------------------------------------

class TestGateOutcome:
    def test_perfect_score_passes(self):
        resp = compute_reliability_score(_perfect_request())
        assert resp.gate_result == GateResult.PASS
        assert resp.policy_score >= PASS_THRESHOLD
        assert resp.reliability_index >= PASS_THRESHOLD
        assert resp.hard_constraint_violations == []

    def test_low_scores_fail(self):
        resp = compute_reliability_score(_failing_request())
        assert resp.gate_result == GateResult.FAIL

    def test_conditional_band(self):
        """A score between 0.78 and 0.85 with no hard violations → conditional."""
        # hallucination = unsupported / (supported+unsupported) = 29/1000 = 0.029 < 0.03
        # safety = 5/1000 = 0.005 < 0.01
        # groundedness = 971/1000 = 0.971
        # task_success = 800/1000 = 0.80
        # robustness = 70/100 = 0.70
        # latency_slo = 750/1000 = 0.75
        # audit = 7/10 = 0.70
        # safety_compliance = 1 - 0.005 = 0.995
        # policy_score = 0.30*0.971 + 0.20*0.80 + 0.15*0.70 + 0.15*0.995 + 0.10*0.75 + 0.10*0.70
        #             = 0.2913 + 0.16 + 0.105 + 0.14925 + 0.075 + 0.07 = 0.85055
        # That's above 0.85, need to lower a bit more.
        # Try robustness=60/100=0.60, latency=700/1000=0.70, audit=6/10=0.60
        # PS = 0.30*0.971 + 0.20*0.80 + 0.15*0.60 + 0.15*0.995 + 0.10*0.70 + 0.10*0.60
        #    = 0.2913 + 0.16 + 0.09 + 0.14925 + 0.07 + 0.06 = 0.82055
        resp = compute_reliability_score(
            ReliabilityScoreRequest(
                total_prompts=1000,
                successful_tasks=800,
                supported_claims=971,
                unsupported_claims=29,  # hallucination = 29/1000 = 0.029 < 0.03
                policy_violations=5,  # safety = 5/1000 = 0.005 < 0.01
                p95_latency_ms=2000.0,
                total_inference_cost_usd=100.0,
                total_requests=1000,
                compliant_requests=700,
                adversarial_tests_total=100,
                adversarial_tests_passed=60,
                required_artifacts=10,
                complete_artifacts=6,
                availability=0.95,
            )
        )
        assert CONDITIONAL_THRESHOLD <= resp.policy_score < PASS_THRESHOLD
        assert resp.gate_result == GateResult.CONDITIONAL
        assert resp.hard_constraint_violations == []


# ---------------------------------------------------------------------------
# Hard-constraint tests
# ---------------------------------------------------------------------------

class TestHardConstraints:
    def test_hallucination_violation(self):
        """Hallucination rate > 0.03 → FAIL regardless of score."""
        resp = compute_reliability_score(
            _perfect_request(
                supported_claims=900,
                unsupported_claims=100,  # rate = 100/1000 = 0.10
            )
        )
        assert resp.gate_result == GateResult.FAIL
        names = [v.constraint for v in resp.hard_constraint_violations]
        assert "HallucinationRate" in names

    def test_safety_violation(self):
        """Safety violation rate > 0.01 → FAIL."""
        resp = compute_reliability_score(
            _perfect_request(policy_violations=20)  # 20/1000 = 0.02
        )
        assert resp.gate_result == GateResult.FAIL
        names = [v.constraint for v in resp.hard_constraint_violations]
        assert "SafetyViolationRate" in names

    def test_both_violations(self):
        resp = compute_reliability_score(
            _perfect_request(
                supported_claims=900,
                unsupported_claims=100,
                policy_violations=20,
            )
        )
        assert resp.gate_result == GateResult.FAIL
        assert len(resp.hard_constraint_violations) == 2

    def test_at_limit_passes(self):
        """Exactly at limit should pass (<=)."""
        # hallucination = unsupported/(supported+unsupported)
        # To get exactly 0.03: unsupported=30, supported=970
        # → 30/(970+30) = 30/1000 = 0.03 ✓
        # safety = policy_violations / total_prompts
        # 10/1000 = 0.01, exactly at limit
        resp = compute_reliability_score(
            _perfect_request(
                total_prompts=1000,
                supported_claims=970,
                unsupported_claims=30,
                policy_violations=10,
            )
        )
        violations = [v.constraint for v in resp.hard_constraint_violations]
        assert "HallucinationRate" not in violations
        assert "SafetyViolationRate" not in violations


# ---------------------------------------------------------------------------
# Sub-score arithmetic
# ---------------------------------------------------------------------------

class TestSubScores:
    def test_groundedness(self):
        resp = compute_reliability_score(
            _perfect_request(supported_claims=800, unsupported_claims=200)
        )
        assert resp.sub_scores.groundedness_score == pytest.approx(0.80, abs=1e-4)
        assert resp.sub_scores.hallucination_rate == pytest.approx(0.20, abs=1e-4)

    def test_task_success_rate(self):
        resp = compute_reliability_score(_perfect_request(successful_tasks=750))
        assert resp.sub_scores.task_success_rate == pytest.approx(0.75, abs=1e-4)

    def test_cost_per_task(self):
        resp = compute_reliability_score(
            _perfect_request(successful_tasks=500, total_inference_cost_usd=100.0)
        )
        assert resp.sub_scores.cost_per_successful_task == pytest.approx(0.20, abs=1e-4)

    def test_cost_per_task_zero_successes(self):
        resp = compute_reliability_score(
            _perfect_request(successful_tasks=0, total_prompts=1)
        )
        assert resp.sub_scores.cost_per_successful_task is None


# ---------------------------------------------------------------------------
# Edge cases — zero denominators
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_claims_defaults_groundedness_to_one(self):
        resp = compute_reliability_score(
            _perfect_request(supported_claims=0, unsupported_claims=0)
        )
        assert resp.sub_scores.groundedness_score == pytest.approx(1.0, abs=1e-4)
        assert resp.sub_scores.hallucination_rate == pytest.approx(0.0, abs=1e-4)

    def test_zero_adversarial_defaults_robustness_to_one(self):
        resp = compute_reliability_score(
            _perfect_request(adversarial_tests_total=0, adversarial_tests_passed=0)
        )
        assert resp.sub_scores.prompt_robustness == pytest.approx(1.0, abs=1e-4)

    def test_zero_requests_defaults_latency_slo_to_one(self):
        resp = compute_reliability_score(
            _perfect_request(total_requests=0, compliant_requests=0)
        )
        assert resp.sub_scores.latency_slo_compliance == pytest.approx(1.0, abs=1e-4)

    def test_zero_artifacts_defaults_audit_to_one(self):
        resp = compute_reliability_score(
            _perfect_request(required_artifacts=0, complete_artifacts=0)
        )
        assert resp.sub_scores.audit_completeness == pytest.approx(1.0, abs=1e-4)

    def test_minimum_valid_request(self):
        """Only mandatory fields, all optional defaults."""
        resp = compute_reliability_score(
            ReliabilityScoreRequest(
                total_prompts=1,
                successful_tasks=1,
                supported_claims=1,
                unsupported_claims=0,
                policy_violations=0,
                p95_latency_ms=100.0,
                total_inference_cost_usd=0.01,
            )
        )
        assert resp.gate_result == GateResult.PASS


# ---------------------------------------------------------------------------
# Composite score equations
# ---------------------------------------------------------------------------

class TestCompositeScores:
    def test_reliability_index_equation(self):
        """Verify RI = 0.30*G + 0.25*T + 0.20*P + 0.15*L + 0.10*A."""
        resp = compute_reliability_score(
            ReliabilityScoreRequest(
                total_prompts=100,
                successful_tasks=90,        # task_success = 0.90
                supported_claims=95,
                unsupported_claims=5,        # groundedness = 0.95
                policy_violations=2,         # safety_viol = 0.02 → compliance = 0.98
                p95_latency_ms=1000.0,
                total_inference_cost_usd=10.0,
                total_requests=100,
                compliant_requests=85,       # latency_slo = 0.85
                adversarial_tests_total=50,
                adversarial_tests_passed=45,
                required_artifacts=10,
                complete_artifacts=9,
                availability=0.995,
            )
        )
        expected_ri = (
            0.30 * 0.95
            + 0.25 * 0.90
            + 0.20 * 0.98    # safety_compliance = 1 - 0.02
            + 0.15 * 0.85
            + 0.10 * 0.995
        )
        assert resp.reliability_index == pytest.approx(expected_ri, abs=1e-4)

    def test_policy_score_equation(self):
        """Verify PS = 0.30*G + 0.20*T + 0.15*R + 0.15*S + 0.10*L + 0.10*A."""
        resp = compute_reliability_score(
            ReliabilityScoreRequest(
                total_prompts=100,
                successful_tasks=90,
                supported_claims=95,
                unsupported_claims=5,
                policy_violations=2,
                p95_latency_ms=1000.0,
                total_inference_cost_usd=10.0,
                total_requests=100,
                compliant_requests=85,
                adversarial_tests_total=50,
                adversarial_tests_passed=45,  # robustness = 0.90
                required_artifacts=10,
                complete_artifacts=9,          # audit = 0.90
                availability=0.995,
            )
        )
        expected_ps = (
            0.30 * 0.95
            + 0.20 * 0.90
            + 0.15 * 0.90
            + 0.15 * 0.98
            + 0.10 * 0.85
            + 0.10 * 0.90
        )
        assert resp.policy_score == pytest.approx(expected_ps, abs=1e-4)


# ---------------------------------------------------------------------------
# NIST AI RMF mapping
# ---------------------------------------------------------------------------

class TestNistMapping:
    def test_pass_mapping(self):
        resp = compute_reliability_score(_perfect_request())
        assert "pass" in resp.nist_rmf.govern.lower()
        assert "no action required" in resp.nist_rmf.manage.lower()

    def test_fail_mapping(self):
        resp = compute_reliability_score(_failing_request())
        assert "fail" in resp.nist_rmf.govern.lower()
        assert "escalation" in resp.nist_rmf.manage.lower()

    def test_all_four_functions_present(self):
        resp = compute_reliability_score(_perfect_request())
        assert resp.nist_rmf.govern
        assert resp.nist_rmf.map
        assert resp.nist_rmf.measure
        assert resp.nist_rmf.manage


# ---------------------------------------------------------------------------
# Rationale
# ---------------------------------------------------------------------------

class TestRationale:
    def test_pass_rationale(self):
        resp = compute_reliability_score(_perfect_request())
        assert "PASSED" in resp.rationale

    def test_fail_rationale_hard_constraint(self):
        resp = compute_reliability_score(
            _perfect_request(supported_claims=900, unsupported_claims=100)
        )
        assert "FAILED" in resp.rationale
        assert "HallucinationRate" in resp.rationale

    def test_conditional_rationale(self):
        # Same data as TestGateOutcome.test_conditional_band
        resp = compute_reliability_score(
            ReliabilityScoreRequest(
                total_prompts=1000,
                successful_tasks=800,
                supported_claims=971,
                unsupported_claims=29,
                policy_violations=5,
                p95_latency_ms=2000.0,
                total_inference_cost_usd=100.0,
                total_requests=1000,
                compliant_requests=700,
                adversarial_tests_total=100,
                adversarial_tests_passed=60,
                required_artifacts=10,
                complete_artifacts=6,
                availability=0.95,
            )
        )
        assert "CONDITIONAL" in resp.rationale
