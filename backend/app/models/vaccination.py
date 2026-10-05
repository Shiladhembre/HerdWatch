from uuid import UUID
from datetime import date
from sqlalchemy import String, ForeignKey, Date, Integer, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity, Attributed


class Vaccination(Entity, Attributed, Base):
    __tablename__ = "vaccinations"
    __table_args__ = (
        CheckConstraint("(animal_id IS NULL) <> (herd_id IS NULL)", name="one_subject"),
        CheckConstraint("dose_number > 0", name="positive_dose"),
        CheckConstraint("next_due_on IS NULL OR next_due_on >= administered_on", name="ordered_dates"),
    )
    animal_id: Mapped[UUID | None] = mapped_column(ForeignKey("animals.id"), index=True)
    herd_id: Mapped[UUID | None] = mapped_column(ForeignKey("herds.id"), index=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    district: Mapped[str] = mapped_column(String(100), index=True)
    village: Mapped[str] = mapped_column(String(150), index=True)
    vaccine_name: Mapped[str] = mapped_column(String(150))
    disease_target: Mapped[str] = mapped_column(String(150))
    dose_number: Mapped[int] = mapped_column(Integer)
    administered_on: Mapped[date] = mapped_column(Date)
    next_due_on: Mapped[date | None] = mapped_column(Date, index=True)
    administered_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    batch_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str] = mapped_column(Text, default="")
