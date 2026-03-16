from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CoordinatorUpdate(BaseModel):
    value: str


class CoordinatorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    bulletin_id: str = Field(alias="bulletinId")
    type: str
    value: Optional[str] = None
