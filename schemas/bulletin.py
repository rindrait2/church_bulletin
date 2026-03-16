from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BulletinCreate(BaseModel):
    id: str
    date: str
    lesson_code: Optional[str] = None
    lesson_title: Optional[str] = None
    sabbath_ends: Optional[str] = None
    next_sabbath: Optional[str] = None


class BulletinUpdate(BaseModel):
    date: Optional[str] = None
    lesson_code: Optional[str] = None
    lesson_title: Optional[str] = None
    sabbath_ends: Optional[str] = None
    next_sabbath: Optional[str] = None


class BulletinRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: str
    lesson_code: Optional[str] = Field(None, alias="lessonCode")
    lesson_title: Optional[str] = Field(None, alias="lessonTitle")
    sabbath_ends: Optional[str] = Field(None, alias="sabbathEnds")
    next_sabbath: Optional[str] = Field(None, alias="nextSabbath")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProgramItemInFull(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    sequence: int
    role: Optional[str] = None
    note: Optional[str] = None
    person: Optional[str] = None
    is_sermon: bool = Field(False, alias="isSermon")


class AnnouncementInFull(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sequence: int
    title: Optional[str] = None
    body: Optional[str] = None
    recurring: bool = False
    pinned: bool = False


class ProgramGrouped(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lesson_study: list[ProgramItemInFull] = Field(default_factory=list, alias="lessonStudy")
    ss_program: list[ProgramItemInFull] = Field(default_factory=list, alias="ssProgram")
    divine_service: list[ProgramItemInFull] = Field(default_factory=list, alias="divineService")


class BulletinFull(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    date: str
    lesson_code: Optional[str] = Field(None, alias="lessonCode")
    lesson_title: Optional[str] = Field(None, alias="lessonTitle")
    sabbath_ends: Optional[str] = Field(None, alias="sabbathEnds")
    next_sabbath: Optional[str] = Field(None, alias="nextSabbath")
    program: ProgramGrouped
    coordinators: dict[str, str]
    announcements: list[AnnouncementInFull]
