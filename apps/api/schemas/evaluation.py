from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator


class EvaluationRunCreate(BaseModel):
    model_id: str
    model_version: str
    prompt_set_id: str
    prompt_set_version: str
    total_prompts: int
    successful_tasks: int
    supported_claims: int
    unsupported_claims: int
    policy_violations: int
    p95_latency_ms: int
    total_inference_cost_usd: Decimal
    prompt_robustness: Decimal = Decimal("1.0")
    availability: Decimal = Decimal("1.0")

    @field_validator("total_prompts", "successful_tasks", "supported_claims",
                     "unsupported_claims", "policy_violations", "p95_latency_ms")
    @classmethod
    def must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("must be >= 0")
        return v

    @field_validator("prompt_robustness", "availability")
    @classmethod
    def must_be_unit_interval(cls, v: Decimal) -> Decimal:
        if not (Decimal("0") <= v <= Decimal("1")):
            raise ValueError("must be between 0 and 1")
        return v


class EvaluationRunResponse(BaseModel):
    evaluation_id: str
    model_id: str
    model_version: str
    prompt_set_id: str
    prompt_set_version: str
    total_prompts: int
    successful_tasks: int
    supported_claims: int
    unsupported_claims: int
    policy_violations: int
    p95_latency_ms: int
    total_inference_cost_usd: Decimal
    prompt_robustness: Decimal
    availability: Decimal
    submitted_at: datetime

    model_config = {"from_attributes": True}
