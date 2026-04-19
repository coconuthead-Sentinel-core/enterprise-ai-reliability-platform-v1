from datetime import datetime
from pydantic import BaseModel


class AuditReportResponse(BaseModel):
    decision_id: str
    evaluation_id: str
    policy_score: float
    result: str
    rationale: str | None = None
    decided_at: datetime
    model_id: str
    model_version: str
    prompt_set_id: str
    prompt_set_version: str
    generated_at: datetime
    report_uri: str
