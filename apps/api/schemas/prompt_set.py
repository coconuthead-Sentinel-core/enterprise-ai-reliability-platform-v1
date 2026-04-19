from datetime import datetime
from pydantic import BaseModel


class PromptSetCreate(BaseModel):
    prompt_set_version: str
    benchmark_suite_id: str


class PromptSetResponse(BaseModel):
    prompt_set_id: str
    prompt_set_version: str
    benchmark_suite_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
