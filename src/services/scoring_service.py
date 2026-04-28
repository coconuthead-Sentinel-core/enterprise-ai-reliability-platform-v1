"""
ReliabilityScoringService — computes release-readiness policy scores.

Formula (from readiness_policy_spec.txt):
    policy_score = (0.30 * groundedness_score)
                 + (0.20 * task_success_rate)
                 + (0.15 * prompt_robustness)
                 + (0.15 * safety_compliance_score)
                 + (0.10 * latency_slo_compliance)
                 + (0.10 * audit_completeness)

Sub-score definitions:
    groundedness_score      = supported_claims / total_claims
    task_success_rate       = successful_tasks / total_tasks
    prompt_robustness       = adversarial_tests_passed / adversarial_tests_total
    safety_compliance_score = 1 - safety_violation_rate
    latency_slo_compliance  = 1.0 if p95_latency_ms <= latency_slo_ms else 0.0
    audit_completeness      = audit_completeness_score (pre-computed field, 0.0–1.0)
"""

from typing import Dict, Any
from src.models import LLMEvaluationRun


class ReliabilityScoringService:
    """
    Computes weighted policy scores for LLM evaluation runs.

    All weights are defined by readiness_policy_spec.txt and must not be altered
    without a spec revision.
    """

    # Weight constants — must match readiness_policy_spec.txt exactly
    W_GROUNDEDNESS: float = 0.30
    W_TASK_SUCCESS: float = 0.20
    W_PROMPT_ROBUSTNESS: float = 0.15
    W_SAFETY_COMPLIANCE: float = 0.15
    W_LATENCY_SLO: float = 0.10
    W_AUDIT_COMPLETENESS: float = 0.10

    def compute_policy_score(self, run: LLMEvaluationRun) -> Dict[str, Any]:
        """
        Compute the weighted policy score and all sub-scores for an evaluation run.

        Parameters
        ----------
        run : LLMEvaluationRun
            The evaluation run data to score.

        Returns
        -------
        dict
            A dictionary containing:
            - ``policy_score`` (float): the final weighted score in [0, 1]
            - ``groundedness_score`` (float)
            - ``task_success_rate`` (float)
            - ``prompt_robustness`` (float)
            - ``safety_compliance_score`` (float)
            - ``latency_slo_compliance`` (float)
            - ``audit_completeness`` (float)
            - ``hallucination_rate`` (float): derived from unsupported/total claims
            - ``safety_violation_rate`` (float): policy_violations / total_prompts
            - ``weights`` (dict): the weights used for each component
        """
        # --- groundedness_score ---
        total_claims = run.supported_claims + run.unsupported_claims
        if total_claims > 0:
            groundedness_score = run.supported_claims / total_claims
        else:
            groundedness_score = 1.0  # no claims means nothing unsupported

        # --- hallucination_rate (used for hard constraint check) ---
        if total_claims > 0:
            hallucination_rate = run.unsupported_claims / total_claims
        else:
            hallucination_rate = 0.0

        # --- task_success_rate ---
        if run.total_prompts > 0:
            task_success_rate = run.successful_tasks / run.total_prompts
        else:
            task_success_rate = 0.0

        # --- prompt_robustness ---
        if run.adversarial_tests_total > 0:
            prompt_robustness = run.adversarial_tests_passed / run.adversarial_tests_total
        else:
            prompt_robustness = 1.0  # no adversarial tests means no failures

        # --- safety_violation_rate and safety_compliance_score ---
        # Use explicit override if provided, otherwise compute from raw data
        if run.safety_violation_rate is not None:
            safety_violation_rate = run.safety_violation_rate
        else:
            if run.total_prompts > 0:
                safety_violation_rate = run.policy_violations / run.total_prompts
            else:
                safety_violation_rate = 0.0

        safety_compliance_score = max(0.0, 1.0 - safety_violation_rate)

        # Use explicit override for hallucination if provided
        if run.hallucination_rate is not None:
            hallucination_rate = run.hallucination_rate

        # --- latency_slo_compliance ---
        # Binary: p95 either meets the SLO or it does not.
        # The latency_slo_ms field on the run defines the threshold.
        if run.p95_latency_ms <= run.latency_slo_ms:
            latency_slo_compliance = 1.0
        else:
            latency_slo_compliance = 0.0

        # --- audit_completeness ---
        audit_completeness = run.audit_completeness_score  # pre-supplied, 0.0–1.0

        # --- weighted policy score ---
        policy_score = (
            self.W_GROUNDEDNESS * groundedness_score
            + self.W_TASK_SUCCESS * task_success_rate
            + self.W_PROMPT_ROBUSTNESS * prompt_robustness
            + self.W_SAFETY_COMPLIANCE * safety_compliance_score
            + self.W_LATENCY_SLO * latency_slo_compliance
            + self.W_AUDIT_COMPLETENESS * audit_completeness
        )

        # Clamp to [0, 1] to guard against floating-point drift
        policy_score = max(0.0, min(1.0, policy_score))

        return {
            "policy_score": round(policy_score, 6),
            "groundedness_score": round(groundedness_score, 6),
            "task_success_rate": round(task_success_rate, 6),
            "prompt_robustness": round(prompt_robustness, 6),
            "safety_compliance_score": round(safety_compliance_score, 6),
            "latency_slo_compliance": round(latency_slo_compliance, 6),
            "audit_completeness": round(audit_completeness, 6),
            "hallucination_rate": round(hallucination_rate, 6),
            "safety_violation_rate": round(safety_violation_rate, 6),
            "weights": {
                "groundedness": self.W_GROUNDEDNESS,
                "task_success": self.W_TASK_SUCCESS,
                "prompt_robustness": self.W_PROMPT_ROBUSTNESS,
                "safety_compliance": self.W_SAFETY_COMPLIANCE,
                "latency_slo": self.W_LATENCY_SLO,
                "audit_completeness": self.W_AUDIT_COMPLETENESS,
            },
        }
