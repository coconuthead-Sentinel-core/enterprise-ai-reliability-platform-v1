"""
EvidenceRegistryService — stores and retrieves evaluation runs with lineage tracking.

MVP implementation uses an in-memory dict store. Each stored entry records
a lineage chain of all versions of that evaluation_id to support immutable
audit trails.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from src.models import LLMEvaluationRun


class EvidenceRegistryService:
    """
    In-memory registry for LLMEvaluationRun evidence entities.

    Maintains a lineage chain per evaluation_id so that any update or
    re-registration of an evaluation produces a traceable history rather
    than a destructive overwrite.
    """

    def __init__(self) -> None:
        """Initialise an empty in-memory store and lineage index."""
        # Primary store: evaluation_id -> latest LLMEvaluationRun
        self._store: Dict[str, LLMEvaluationRun] = {}

        # Lineage store: evaluation_id -> ordered list of (timestamp, snapshot dict)
        self._lineage: Dict[str, List[Dict[str, Any]]] = {}

        # Connector metadata store: evaluation_id -> connector payload metadata
        self._connector_metadata: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def register(
        self,
        run: LLMEvaluationRun,
        connector_metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMEvaluationRun:
        """
        Register or update an evaluation run in the evidence registry.

        If the evaluation_id already exists, the existing entry is
        appended to the lineage chain before the new version is stored.

        Parameters
        ----------
        run : LLMEvaluationRun
            The evaluation run to register.
        connector_metadata : dict, optional
            Connector-gateway metadata to store alongside the run.

        Returns
        -------
        LLMEvaluationRun
            The registered run (unchanged, returned for convenience).
        """
        eid = run.evaluation_id

        # If this evaluation_id was previously registered, record the old
        # version in the lineage chain before overwriting.
        if eid in self._store:
            existing = self._store[eid]
            self._append_lineage(eid, existing)

        self._store[eid] = run

        # Initialise lineage list for brand-new entries
        if eid not in self._lineage:
            self._lineage[eid] = []

        # Always record the current version in lineage so the chain is complete
        self._append_lineage(eid, run)

        if connector_metadata:
            self._connector_metadata[eid] = connector_metadata

        return run

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get(self, evaluation_id: str) -> Optional[LLMEvaluationRun]:
        """
        Retrieve the latest version of an evaluation run by its ID.

        Parameters
        ----------
        evaluation_id : str
            The unique identifier of the evaluation run.

        Returns
        -------
        LLMEvaluationRun or None
            The run if found, else None.
        """
        return self._store.get(evaluation_id)

    def list_all(self) -> List[LLMEvaluationRun]:
        """
        Return a list of all registered evaluation runs (latest versions).

        Returns
        -------
        list of LLMEvaluationRun
        """
        return list(self._store.values())

    def get_lineage(self, evaluation_id: str) -> List[Dict[str, Any]]:
        """
        Return the full lineage chain for an evaluation_id.

        Each entry in the chain is a dict with ``recorded_at`` and ``snapshot``
        keys, where ``snapshot`` is the serialised run at that point in time.

        Parameters
        ----------
        evaluation_id : str

        Returns
        -------
        list of dict
            Ordered oldest-first lineage chain, or empty list if not found.
        """
        return self._lineage.get(evaluation_id, [])

    def get_connector_metadata(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the connector-gateway metadata stored with an evaluation run.

        Parameters
        ----------
        evaluation_id : str

        Returns
        -------
        dict or None
        """
        return self._connector_metadata.get(evaluation_id)

    def exists(self, evaluation_id: str) -> bool:
        """Return True if the evaluation_id is registered."""
        return evaluation_id in self._store

    def count(self) -> int:
        """Return the total number of registered evaluation runs."""
        return len(self._store)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _append_lineage(self, evaluation_id: str, run: LLMEvaluationRun) -> None:
        """Append a serialised snapshot of *run* to the lineage chain."""
        if evaluation_id not in self._lineage:
            self._lineage[evaluation_id] = []
        self._lineage[evaluation_id].append(
            {
                "recorded_at": datetime.utcnow().isoformat(),
                "snapshot": run.model_dump(),
            }
        )
