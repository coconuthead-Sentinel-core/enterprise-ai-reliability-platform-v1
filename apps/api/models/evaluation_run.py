import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, Integer, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class LLMEvaluationRun(Base):
    __tablename__ = "llm_evaluation_runs"

    evaluation_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    model_id: Mapped[str] = mapped_column(
        String, ForeignKey("llm_model_versions.model_id"), nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_set_id: Mapped[str] = mapped_column(
        String, ForeignKey("prompt_set_versions.prompt_set_id"), nullable=False
    )
    prompt_set_version: Mapped[str] = mapped_column(String(64), nullable=False)
    total_prompts: Mapped[int] = mapped_column(Integer, nullable=False)
    successful_tasks: Mapped[int] = mapped_column(Integer, nullable=False)
    supported_claims: Mapped[int] = mapped_column(Integer, nullable=False)
    unsupported_claims: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_violations: Mapped[int] = mapped_column(Integer, nullable=False)
    p95_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    total_inference_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False
    )
    prompt_robustness: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("1.0")
    )
    availability: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("1.0")
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
