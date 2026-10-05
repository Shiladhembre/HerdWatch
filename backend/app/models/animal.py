from uuid import UUID
from datetime import date
from sqlalchemy import String, ForeignKey, Date, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity, Located, Attributed


class Animal(Entity, Located, Attributed, Base):
    __tablename__ = "animals"
    __table_args__ = (CheckConstraint("approximate_age >= 0", name="positive_age"),)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    animal_tag: Mapped[str] = mapped_column(String(80), unique=True)
    species: Mapped[str] = mapped_column(String(30), index=True)
    breed: Mapped[str] = mapped_column(String(100), default="")
    sex: Mapped[str] = mapped_column(String(20), default="Unknown")
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    approximate_age: Mapped[float | None] = mapped_column(Float)
    pregnancy_status: Mapped[str] = mapped_column(String(40), default="Unknown")
    health_status: Mapped[str] = mapped_column(String(50), default="Needs review", index=True)


class AnimalRecord(Entity, Base):
    __tablename__ = "animal_records"
    animal_id: Mapped[UUID] = mapped_column(ForeignKey("animals.id"), index=True)
    recorded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    record_type: Mapped[str] = mapped_column(String(50))
    recorded_on: Mapped[date] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(String(5000))
