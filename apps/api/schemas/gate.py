from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel


class GateEvaluationRequest(BaseModel):
    evaluation_id: str
    policy_id: str


class GateDecisionResponse(BaseModel):
    decision_id: str
    evaluation_id: str
    policy_score: Decimal
    result: Literal["pass", "conditional", "fail"]
    rationale: str | None = None
    decided_at: datetime

    model_config = {"from_attributes": True}
