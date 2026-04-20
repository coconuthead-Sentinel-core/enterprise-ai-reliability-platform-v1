"""Real database layer - SQLAlchemy ORM."""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Float, Integer, String, Text, create_engine,
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
    created_at = Column(DateTime, default=_utcnow, nullable=False)


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


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
