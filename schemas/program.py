from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProgramItemCreate(BaseModel):
    block: str
    sequence: int
    role: Optional[str] = None
    note: Optional[str] = None
    person: Optional[str] = None
    is_sermon: bool = False


class ProgramItemUpdate(BaseModel):
    block: Optional[str] = None
    sequence: Optional[int] = None
    role: Optional[str] = None
    note: Optional[str] = None
    person: Optional[str] = None
    is_sermon: Optional[bool] = None


class ProgramItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    bulletin_id: str = Field(alias="bulletinId")
    block: str
    sequence: int
    role: Optional[str] = None
    note: Optional[str] = None
    person: Optional[str] = None
    is_sermon: bool = Field(False, alias="isSermon")


class ReorderItem(BaseModel):
    id: int
    sequence: int
