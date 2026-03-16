from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MemberRoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str


class MemberCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    active: bool = True
    roles: list[str] = []


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    active: Optional[bool] = None
    roles: Optional[list[str]] = None


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None
    roles: list[MemberRoleSchema] = []
