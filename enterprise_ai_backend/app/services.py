"""Middle layer - pure business logic + persistence helpers."""
import hashlib
import math
from typing import Optional

from sqlalchemy.orm import Session

from . import database, schemas


# ---------- Reliability ----------

def compute_reliability(
    db: Session,
    payload: schemas.ReliabilityInput,
) -> database.ReliabilityComputation:
    availability = payload.mtbf_hours / (payload.mtbf_hours + payload.mttr_hours)
    failure_rate = 1.0 / payload.mtbf_hours
    reliability = math.exp(-payload.mission_time_hours / payload.mtbf_hours)
    expected_failures = payload.mission_time_hours / payload.mtbf_hours

    record = database.ReliabilityComputation(
        mtbf_hours=payload.mtbf_hours,
        mttr_hours=payload.mttr_hours,
        mission_time_hours=payload.mission_time_hours,
        availability=round(availability, 8),
        reliability=round(reliability, 8),
        failure_rate_per_hour=round(failure_rate, 10),
        expected_failures=round(expected_failures, 8),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_reliability(db: Session, limit: int = 50):
    return (
        db.query(database.ReliabilityComputation)
        .order_by(database.ReliabilityComputation.id.desc())
        .limit(limit)
        .all()
    )


# ---------- Hash ----------

def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------- Assessments (NIST AI RMF) ----------

# Shared policy - re-exported from libs/policy/scoring.py too.
FUNCTION_WEIGHTS = {
    "govern": 0.25,
    "map": 0.25,
    "measure": 0.25,
    "manage": 0.25,
}


def risk_tier(overall: float) -> str:
    if overall >= 80:
        return "LOW"
    if overall >= 60:
        return "MEDIUM"
    return "HIGH"


def create_assessment(
    db: Session,
    payload: schemas.AssessmentInput,
) -> database.Assessment:
    overall = (
        payload.govern_score * FUNCTION_WEIGHTS["govern"]
        + payload.map_score * FUNCTION_WEIGHTS["map"]
        + payload.measure_score * FUNCTION_WEIGHTS["measure"]
        + payload.manage_score * FUNCTION_WEIGHTS["manage"]
    )
    record = database.Assessment(
        system_name=payload.system_name,
        owner=payload.owner,
        govern_score=payload.govern_score,
        map_score=payload.map_score,
        measure_score=payload.measure_score,
        manage_score=payload.manage_score,
        overall_score=round(overall, 4),
        risk_tier=risk_tier(overall),
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_assessments(db: Session, limit: int = 50):
    return (
        db.query(database.Assessment)
        .order_by(database.Assessment.id.desc())
        .limit(limit)
        .all()
    )


def get_assessment(db: Session, assessment_id: int) -> Optional[database.Assessment]:
    return db.query(database.Assessment).filter_by(id=assessment_id).first()
