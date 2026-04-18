"""Pydantic request / response schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------- Auth ----------

class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=8, max_length=200)

    @field_validator("email")
    @classmethod
    def _looks_like_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@", 1)[-1]:
            raise ValueError("email must contain '@' and a domain")
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str
    created_at: datetime


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_env: str
    app_version: str
    python_version: str
    platform: str
    uptime_seconds: float
    server_time_utc: str
    database: str


# ---------- Reliability ----------

class ReliabilityInput(BaseModel):
    mtbf_hours: float = Field(..., gt=0)
    mttr_hours: float = Field(..., gt=0)
    mission_time_hours: float = Field(..., gt=0)


class ReliabilityOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    mtbf_hours: float
    mttr_hours: float
    mission_time_hours: float
    availability: float
    reliability: float
    failure_rate_per_hour: float
    expected_failures: float
    created_at: datetime


# ---------- Hash ----------

class HashInput(BaseModel):
    text: str


class HashOutput(BaseModel):
    text: str
    sha256: str
    length: int


# ---------- Assessments (NIST AI RMF) ----------

class AssessmentInput(BaseModel):
    system_name: str = Field(..., min_length=1, max_length=200)
    owner: str = Field(..., min_length=1, max_length=200)
    govern_score: int = Field(..., ge=0, le=100)
    map_score: int = Field(..., ge=0, le=100)
    measure_score: int = Field(..., ge=0, le=100)
    manage_score: int = Field(..., ge=0, le=100)
    notes: Optional[str] = None


class AssessmentOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    system_name: str
    owner: str
    govern_score: int
    map_score: int
    measure_score: int
    manage_score: int
    overall_score: float
    risk_tier: str
    notes: Optional[str] = None
    created_at: datetime


# ---------- AI / ML ----------

class AnomalyInput(BaseModel):
    records: List[List[float]] = Field(
        ...,
        min_length=2,
        description="List of feature vectors (2+ records required)",
    )
    contamination: float = Field(0.1, gt=0, lt=0.5)


class AnomalyOutput(BaseModel):
    n_trained_on: int
    n_scored: int
    predictions: List[int]
    scores: List[float]
    anomaly_count: int
    model: str
    record_ids: Optional[List[int]] = None
