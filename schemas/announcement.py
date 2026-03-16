from typing import Optional

from pydantic import BaseModel, ConfigDict


class AnnouncementCreate(BaseModel):
    sequence: int
    title: Optional[str] = None
    body: Optional[str] = None
    recurring: bool = False
    pinned: bool = False


class AnnouncementUpdate(BaseModel):
    sequence: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None
    recurring: Optional[bool] = None
    pinned: Optional[bool] = None


class AnnouncementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bulletin_id: str
    sequence: int
    title: Optional[str] = None
    body: Optional[str] = None
    recurring: bool = False
    pinned: bool = False
