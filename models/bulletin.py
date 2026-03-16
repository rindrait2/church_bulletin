from datetime import datetime, UTC

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Bulletin(Base):
    __tablename__ = "bulletins"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    date: Mapped[str] = mapped_column(String(50), nullable=False)
    lesson_code: Mapped[str | None] = mapped_column(String(20))
    lesson_title: Mapped[str | None] = mapped_column(String(200))
    sabbath_ends: Mapped[str | None] = mapped_column(String(20))
    next_sabbath: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    program_items = relationship("ProgramItem", back_populates="bulletin", cascade="all, delete-orphan")
    coordinators = relationship("Coordinator", back_populates="bulletin", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="bulletin", cascade="all, delete-orphan")
