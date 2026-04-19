import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, DateTime, Numeric, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class GateResult(str, enum.Enum):
    PASS = "pass"
    CONDITIONAL = "conditional"
    FAIL = "fail"


class GateDecision(Base):
    __tablename__ = "gate_decisions"

    decision_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    evaluation_id: Mapped[str] = mapped_column(
        String, ForeignKey("llm_evaluation_runs.evaluation_id"), nullable=False
    )
    policy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    result: Mapped[GateResult] = mapped_column(Enum(GateResult), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
