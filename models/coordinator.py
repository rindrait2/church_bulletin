from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Coordinator(Base):
    __tablename__ = "coordinators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bulletin_id: Mapped[str] = mapped_column(String(20), ForeignKey("bulletins.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[str | None] = mapped_column(Text)

    bulletin = relationship("Bulletin", back_populates="coordinators")
