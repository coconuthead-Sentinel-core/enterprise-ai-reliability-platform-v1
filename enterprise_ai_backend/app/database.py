"""Real database layer - SQLAlchemy ORM."""
import json
from datetime import datetime, timezone
from typing import List

from sqlalchemy import (
    Column, DateTime, Float, Integer, String, Text, create_engine, inspect, text,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """Real user record. Passwords are hashed with bcrypt before storage."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")  # user | admin
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class ReliabilityComputation(Base):
    __tablename__ = "reliability_computations"

    id = Column(Integer, primary_key=True)
    mtbf_hours = Column(Float, nullable=False)
    mttr_hours = Column(Float, nullable=False)
    mission_time_hours = Column(Float, nullable=False)
    availability = Column(Float, nullable=False)
    reliability = Column(Float, nullable=False)
    failure_rate_per_hour = Column(Float, nullable=False)
    expected_failures = Column(Float, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True)
    system_name = Column(String(200), nullable=False)
    owner = Column(String(200), nullable=False)
    govern_score = Column(Integer, nullable=False)
    map_score = Column(Integer, nullable=False)
    measure_score = Column(Integer, nullable=False)
    manage_score = Column(Integer, nullable=False)
    overall_score = Column(Float, nullable=False)
    risk_tier = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    # Sprint 3, E3-S2: policy gate decision persisted alongside the record so
    # the risk_tier and the gate outcome never drift out of sync. Nullable
    # for compatibility with pre-E3-S2 rows (older DBs replayed into the new
    # schema just see ``None`` here).
    gate_decision = Column(String(20), nullable=True)
    gate_reasons_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    @property
    def gate_reasons(self) -> List[dict]:
        """Deserialize ``gate_reasons_json`` so Pydantic ``from_attributes``
        can pick up a list of ``PolicyReason`` objects without extra glue."""
        if not self.gate_reasons_json:
            return []
        try:
            return json.loads(self.gate_reasons_json)
        except (TypeError, ValueError):
            return []


class ReliabilityScoreRecord(Base):
    """One persisted weighted composite reliability score.

    Populated automatically by ``POST /reliability/score`` and
    ``POST /reliability/score/explain`` (Sprint 2, E2-S3) so
    ``GET /reliability/score/history`` can return a trend over time
    without the caller having to re-submit the inputs.
    """

    __tablename__ = "reliability_score_records"

    id = Column(Integer, primary_key=True)
    system_name = Column(String(200), nullable=False, index=True)
    composite_score = Column(Float, nullable=False)
    tier = Column(String(20), nullable=False)
    weights_normalized = Column(Integer, nullable=False)  # 0/1 boolean
    # Serialized list[ReliabilityScoreComponent] for audit / replay.
    components_json = Column(Text, nullable=False)
    nist_govern = Column(Float, nullable=True)
    nist_map = Column(Float, nullable=True)
    nist_measure = Column(Float, nullable=True)
    nist_manage = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)


class PolicyEvaluationRecord(Base):
    """One persisted call to ``POST /policy/evaluate`` (Sprint 3, E3-S3).

    Stores the full audit trail -- request payload, thresholds applied,
    decision, reasons -- so ``GET /policy/history`` can return a trend
    over time and so a later review can replay the exact inputs that
    produced any given decision.
    """

    __tablename__ = "policy_evaluation_records"

    id = Column(Integer, primary_key=True)
    system_name = Column(String(200), nullable=False, index=True)
    decision = Column(String(20), nullable=False)  # allow / warn / block
    composite_score = Column(Float, nullable=False)
    tier = Column(String(20), nullable=False)
    # Serialized request + outcome for audit / replay.
    thresholds_json = Column(Text, nullable=False)
    reasons_json = Column(Text, nullable=False)
    score_input_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)

    @property
    def reasons(self) -> List[dict]:
        """Deserialize ``reasons_json`` so Pydantic ``from_attributes``
        materializes a list of ``PolicyReason`` objects."""
        if not self.reasons_json:
            return []
        try:
            return json.loads(self.reasons_json)
        except (TypeError, ValueError):
            return []

    @property
    def thresholds(self) -> dict:
        """Deserialize ``thresholds_json`` so Pydantic ``from_attributes``
        materializes a :class:`schemas.PolicyThresholds`."""
        if not self.thresholds_json:
            return {}
        try:
            return json.loads(self.thresholds_json)
        except (TypeError, ValueError):
            return {}


def _apply_sqlite_compat_migrations(bind) -> None:
    """Patch old local SQLite files forward without a full migration stack.

    The repo does not yet ship Alembic migrations. For the laptop/dev flow we
    still need older SQLite databases to survive new assessment-gate fields
    landing in code, otherwise startup succeeds until the first ORM write reads
    or inserts against missing columns.
    """
    if bind.dialect.name != "sqlite":
        return

    inspector = inspect(bind)
    if not inspector.has_table("assessments"):
        return

    columns = {column["name"] for column in inspector.get_columns("assessments")}
    statements = []
    if "gate_decision" not in columns:
        statements.append(
            "ALTER TABLE assessments ADD COLUMN gate_decision VARCHAR(20)"
        )
    if "gate_reasons_json" not in columns:
        statements.append(
            "ALTER TABLE assessments ADD COLUMN gate_reasons_json TEXT"
        )

    if not statements:
        return

    with bind.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def init_db(bind=engine):
    Base.metadata.create_all(bind=bind)
    _apply_sqlite_compat_migrations(bind)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
