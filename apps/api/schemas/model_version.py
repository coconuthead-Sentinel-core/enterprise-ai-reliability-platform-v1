from datetime import datetime
from pydantic import BaseModel


class ModelVersionCreate(BaseModel):
    provider: str
    model_name: str
    model_version: str


class ModelVersionResponse(BaseModel):
    model_id: str
    provider: str
    model_name: str
    model_version: str
    registered_at: datetime

    model_config = {"from_attributes": True}
