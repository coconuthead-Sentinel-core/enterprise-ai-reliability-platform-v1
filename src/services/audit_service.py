"""
AuditReportingService — generates immutable audit reports and decision summaries.

Reports are produced as dicts (and AuditReport Pydantic objects) that include
a timestamp, full decision trail, all evidence references, connector metadata,
and a SHA-256 integrity hash to guarantee immutability.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.models import AuditReport, GateDecision, LLMEvaluationRun


class AuditReportingService:
    """
    Produces immutable audit exports for completed evaluation gate cycles.

    Each report captures:
        - A snapshot of the LLMEvaluationRun at report time
        - The full ordered decision trail (all GateDecisions for this run)
        - Lineage references from EvidenceRegistryService
        - Original connector-gateway metadata
        - A SHA-256 hash of all report contents for integrity verification
    """

    def generate_report(
        self,
        run: LLMEvaluationRun,
        decisions: List[GateDecision],
        lineage_refs: Optional[List[Dict[str, Any]]] = None,
        connector_metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditReport:
        """
        Generate an immutable audit report for an evaluation run.

        Parameters
        ----------
        run : LLMEvaluationRun
            The evaluation run being audited.
        decisions : list of GateDecision
            All gate decisions made for this evaluation, ordered chronologically.
        lineage_refs : list of dict, optional
            Lineage chain entries from EvidenceRegistryService.
        connector_metadata : dict, optional
            Original connector-gateway metadata for this run.

        Returns
        -------
        AuditReport
            The immutable audit report with integrity hash.
        """
        report_id = self._generate_report_id(run.evaluation_id)
        generated_at = datetime.utcnow()

        # Serialise the evaluation run snapshot
        evaluation_snapshot = self._serialise_run(run)

        # Serialise the decision trail
        decision_trail = [self._serialise_decision(d) for d in decisions]

        # Extract lineage reference strings
        evidence_references = self._extract_evidence_references(lineage_refs or [])

        # Use connector metadata if provided
        meta = connector_metadata or {}

        # Build the canonical report content dict for hashing
        report_content = {
            "report_id": report_id,
            "generated_at": generated_at.isoformat(),
            "evaluation_snapshot": evaluation_snapshot,
            "decision_trail": decision_trail,
            "evidence_references": evidence_references,
            "connector_metadata": meta,
        }

        immutability_hash = self._compute_hash(report_content)

        return AuditReport(
            report_id=report_id,
            evaluation_id=run.evaluation_id,
            generated_at=generated_at,
            evaluation_snapshot=evaluation_snapshot,
            decision_trail=decision_trail,
            evidence_references=evidence_references,
            connector_metadata=meta,
            immutability_hash=immutability_hash,
        )

    def verify_integrity(self, report: AuditReport) -> bool:
        """
        Verify the integrity of an existing AuditReport by recomputing its hash.

        Parameters
        ----------
        report : AuditReport

        Returns
        -------
        bool
            True if the recomputed hash matches ``report.immutability_hash``.
        """
        report_content = {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat()
            if isinstance(report.generated_at, datetime)
            else report.generated_at,
            "evaluation_snapshot": report.evaluation_snapshot,
            "decision_trail": report.decision_trail,
            "evidence_references": report.evidence_references,
            "connector_metadata": report.connector_metadata,
        }
        expected_hash = self._compute_hash(report_content)
        return expected_hash == report.immutability_hash

    def generate_decision_summary(
        self, decision: GateDecision, run: LLMEvaluationRun
    ) -> Dict[str, Any]:
        """
        Generate a compact decision summary dict for API responses.

        Parameters
        ----------
        decision : GateDecision
        run : LLMEvaluationRun

        Returns
        -------
        dict
        """
        return {
            "decision_id": decision.decision_id,
            "evaluation_id": decision.evaluation_id,
            "result": decision.result,
            "policy_score": decision.policy_score,
            "decided_at": decision.decided_at.isoformat()
            if isinstance(decision.decided_at, datetime)
            else decision.decided_at,
            "hard_constraints_passed": decision.hard_constraints_passed,
            "sub_scores": {
                "groundedness_score": decision.groundedness_score,
                "task_success_rate": decision.task_success_rate,
                "prompt_robustness": decision.prompt_robustness,
                "safety_compliance_score": decision.safety_compliance_score,
                "latency_slo_compliance": decision.latency_slo_compliance,
                "audit_completeness": decision.audit_completeness,
            },
            "hard_constraint_actuals": {
                "hallucination_rate": decision.hallucination_rate_actual,
                "safety_violation_rate": decision.safety_violation_rate_actual,
                "critical_vuln_count": run.critical_vuln_count,
                "compliance_artifacts_complete": run.compliance_artifacts_complete,
            },
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_report_id(evaluation_id: str) -> str:
        """Generate a deterministic report ID from the evaluation ID and timestamp."""
        import uuid
        return f"RPT-{str(uuid.uuid4())[:8].upper()}-{evaluation_id[:8].upper()}"

    @staticmethod
    def _serialise_run(run: LLMEvaluationRun) -> Dict[str, Any]:
        """Return a JSON-serialisable dict snapshot of the evaluation run."""
        data = run.model_dump()
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    @staticmethod
    def _serialise_decision(decision: GateDecision) -> Dict[str, Any]:
        """Return a JSON-serialisable dict of a gate decision."""
        data = decision.model_dump()
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    @staticmethod
    def _extract_evidence_references(lineage_refs: List[Dict[str, Any]]) -> List[str]:
        """
        Extract concise reference strings from lineage chain entries.

        Each lineage entry is summarised as
        ``"<evaluation_id>@<recorded_at>"`` for compact storage.
        """
        refs = []
        for entry in lineage_refs:
            recorded_at = entry.get("recorded_at", "unknown")
            snapshot = entry.get("snapshot", {})
            evaluation_id = snapshot.get("evaluation_id", "unknown")
            refs.append(f"{evaluation_id}@{recorded_at}")
        return refs

    @staticmethod
    def _compute_hash(content: Dict[str, Any]) -> str:
        """
        Compute a SHA-256 hash of the canonical JSON representation of *content*.

        Uses sorted keys and no extra whitespace to ensure deterministic output.
        """
        canonical = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
