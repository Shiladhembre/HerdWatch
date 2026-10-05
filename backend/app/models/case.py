from uuid import UUID
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Integer, Date, Boolean, CheckConstraint, UniqueConstraint, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity, Located, Attributed


class Case(Entity, Located, Attributed, Base):
    __tablename__ = "cases"
    __table_args__ = (
        CheckConstraint("(animal_id IS NULL) <> (herd_id IS NULL)", name="one_subject"),
        CheckConstraint(
            "affected_count > 0 AND death_count >= 0 AND death_count <= affected_count", name="valid_counts"
        ),
        UniqueConstraint("reporter_id", "client_record_id"),
    )
    case_reference: Mapped[str] = mapped_column(String(40), unique=True)
    reporter_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    animal_id: Mapped[UUID | None] = mapped_column(ForeignKey("animals.id"), index=True)
    herd_id: Mapped[UUID | None] = mapped_column(ForeignKey("herds.id"), index=True)
    species: Mapped[str] = mapped_column(String(30), index=True)
    symptom_started_on: Mapped[date] = mapped_column(Date)
    affected_count: Mapped[int] = mapped_column(Integer)
    death_count: Mapped[int] = mapped_column(Integer, default=0)
    observed_symptoms: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(20), default="ROUTINE")
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="REPORTED", index=True)
    assigned_veterinarian_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str] = mapped_column(String(10), default="LOW", index=True)
    suspected_disease: Mapped[str | None] = mapped_column(String(150), index=True)
    clinical_assessment: Mapped[str | None] = mapped_column(Text)
    client_record_id: Mapped[str | None] = mapped_column(String(100))
    request_hash: Mapped[str | None] = mapped_column(String(64))
    created_offline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Attachment(Entity, Base):
    __tablename__ = "attachments"
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id"), index=True)
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    storage_key: Mapped[str] = mapped_column(String(150), unique=True)
    content_type: Mapped[str] = mapped_column(String(80))
    size_bytes: Mapped[int] = mapped_column(Integer)
