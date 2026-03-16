from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class ProgramItem(Base):
    __tablename__ = "program_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bulletin_id: Mapped[str] = mapped_column(String(20), ForeignKey("bulletins.id", ondelete="CASCADE"), nullable=False)
    block: Mapped[str] = mapped_column(String(30), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str | None] = mapped_column(String(100))
    note: Mapped[str | None] = mapped_column(String(200))
    person: Mapped[str | None] = mapped_column(String(200))
    is_sermon: Mapped[bool] = mapped_column(Boolean, default=False)

    bulletin = relationship("Bulletin", back_populates="program_items")
