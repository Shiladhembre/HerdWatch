from uuid import UUID
from sqlalchemy import String, ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity, Located, Attributed


class Herd(Entity, Located, Attributed, Base):
    __tablename__ = "herds"
    __table_args__ = (CheckConstraint("animal_count > 0", name="positive_count"),)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    herd_name: Mapped[str] = mapped_column(String(150))
    species: Mapped[str] = mapped_column(String(30), index=True)
    animal_count: Mapped[int] = mapped_column(Integer)
