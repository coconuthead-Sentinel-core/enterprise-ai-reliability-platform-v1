"""
ConnectorGateway — authenticates and validates external evidence payloads.

Validates incoming evidence payloads against the 10-field metadata schema
required by the EARP connector specification:
    node_id, node_type, title, owner_role, source_system,
    created_utc, updated_utc, zone_state, entropy_state, anchor_ref
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone


# Required metadata fields defined by the connector YAML schema
REQUIRED_METADATA_FIELDS: List[str] = [
    "node_id",
    "node_type",
    "title",
    "owner_role",
    "source_system",
    "created_utc",
    "updated_utc",
    "zone_state",
    "entropy_state",
    "anchor_ref",
]

# Allowed node_type values
VALID_NODE_TYPES: List[str] = [
    "evaluation_run",
    "model_version",
    "prompt_set",
    "gate_decision",
    "audit_report",
    "evidence_artifact",
]

# Allowed zone_state values
VALID_ZONE_STATES: List[str] = [
    "development",
    "staging",
    "production",
    "archived",
    "quarantine",
]

# Allowed entropy_state values
VALID_ENTROPY_STATES: List[str] = [
    "stable",
    "degrading",
    "volatile",
    "unknown",
]


class ConnectorValidationError(ValueError):
    """Raised when an incoming evidence payload fails connector validation."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__(f"Connector validation failed: {'; '.join(errors)}")


class ConnectorGateway:
    """
    Validates and authenticates external evidence payloads before they
    enter the EvidenceRegistryService.

    Validation steps:
        1. Presence check — all 10 required metadata fields must be present.
        2. Type/value checks — node_type, zone_state, entropy_state must be
           from the allowed value lists.
        3. Timestamp format checks — created_utc and updated_utc must be
           valid ISO-8601 UTC strings.
        4. Non-empty string checks — all string fields must be non-blank.
    """

    def validate(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a raw evidence payload dict against the connector schema.

        Parameters
        ----------
        payload : dict
            The incoming payload (typically the ``dict()`` of an
            ``EvaluationRequest``).

        Returns
        -------
        (is_valid, errors) : Tuple[bool, List[str]]
            ``is_valid`` is True only when ``errors`` is empty.
        """
        errors: List[str] = []

        # 1. Presence check
        for field in REQUIRED_METADATA_FIELDS:
            if field not in payload:
                errors.append(f"Missing required metadata field: '{field}'")

        # If fields are missing we cannot do further checks safely
        if errors:
            return False, errors

        # 2. Non-empty string check for all metadata fields
        for field in REQUIRED_METADATA_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"Field '{field}' must be a non-empty string")

        # 3. Controlled-vocabulary checks
        node_type = payload.get("node_type", "")
        if node_type and node_type not in VALID_NODE_TYPES:
            errors.append(
                f"node_type '{node_type}' is not valid. "
                f"Allowed values: {VALID_NODE_TYPES}"
            )

        zone_state = payload.get("zone_state", "")
        if zone_state and zone_state not in VALID_ZONE_STATES:
            errors.append(
                f"zone_state '{zone_state}' is not valid. "
                f"Allowed values: {VALID_ZONE_STATES}"
            )

        entropy_state = payload.get("entropy_state", "")
        if entropy_state and entropy_state not in VALID_ENTROPY_STATES:
            errors.append(
                f"entropy_state '{entropy_state}' is not valid. "
                f"Allowed values: {VALID_ENTROPY_STATES}"
            )

        # 4. ISO-8601 timestamp validation
        for ts_field in ("created_utc", "updated_utc"):
            ts_value = payload.get(ts_field, "")
            if ts_value and not self._is_valid_iso8601(ts_value):
                errors.append(
                    f"Field '{ts_field}' must be a valid ISO-8601 UTC timestamp "
                    f"(e.g. '2026-04-24T12:00:00Z'). Got: '{ts_value}'"
                )

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_or_raise(self, payload: Dict[str, Any]) -> None:
        """
        Validate a payload and raise ``ConnectorValidationError`` on failure.

        Parameters
        ----------
        payload : dict

        Raises
        ------
        ConnectorValidationError
            If validation fails.
        """
        is_valid, errors = self.validate(payload)
        if not is_valid:
            raise ConnectorValidationError(errors)

    def extract_metadata(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract and return only the 10 connector metadata fields from a payload.

        Parameters
        ----------
        payload : dict

        Returns
        -------
        dict
            A dict containing only the REQUIRED_METADATA_FIELDS keys.
        """
        return {field: payload[field] for field in REQUIRED_METADATA_FIELDS if field in payload}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_valid_iso8601(value: str) -> bool:
        """
        Return True if *value* can be parsed as an ISO-8601 UTC timestamp.

        Accepts formats ending in 'Z' or '+00:00'.
        """
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S+00:00",
            "%Y-%m-%dT%H:%M:%S.%f+00:00",
            "%Y-%m-%dT%H:%M:%S",
        ]
        for fmt in formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        return False
