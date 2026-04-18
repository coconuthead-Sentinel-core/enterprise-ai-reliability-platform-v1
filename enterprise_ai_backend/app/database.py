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


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
