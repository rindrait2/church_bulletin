from typing import Optional

from pydantic import BaseModel, ConfigDict


class CalendarEventCreate(BaseModel):
    day: str
    time: str
    name: str
    location: Optional[str] = None
    active: bool = True


class CalendarEventUpdate(BaseModel):
    day: Optional[str] = None
    time: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    active: Optional[bool] = None


class CalendarEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day: str
    time: str
    name: str
    location: Optional[str] = None
    active: bool = True
