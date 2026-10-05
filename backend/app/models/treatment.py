from uuid import UUID
from datetime import date
from sqlalchemy import ForeignKey, String, Text, Date, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity, Attributed


class Treatment(Entity, Attributed, Base):
    __tablename__ = "treatments"
    __table_args__ = (CheckConstraint("ended_on IS NULL OR ended_on >= started_on", name="ordered_dates"),)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id"), index=True)
    animal_id: Mapped[UUID | None] = mapped_column(ForeignKey("animals.id"))
    veterinarian_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    district: Mapped[str] = mapped_column(String(100), index=True)
    treatment_description: Mapped[str] = mapped_column(Text)
    medication: Mapped[str | None] = mapped_column(String(300))
    dosage: Mapped[str | None] = mapped_column(String(300))
    started_on: Mapped[date] = mapped_column(Date)
    ended_on: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(Text, default="")
