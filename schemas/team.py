from typing import Optional

from pydantic import BaseModel, ConfigDict


class TeamCreate(BaseModel):
    name: str
    type: Optional[str] = None
    active: bool = True


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    active: Optional[bool] = None


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: Optional[str] = None
    active: bool = True
