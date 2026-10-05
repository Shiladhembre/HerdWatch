from uuid import UUID
from datetime import date
from sqlalchemy import ForeignKey, String, Text, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity, Attributed


class LabReferral(Entity, Attributed, Base):
    __tablename__ = "lab_referrals"
    sample_reference: Mapped[str] = mapped_column(String(40), unique=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id"), index=True)
    animal_id: Mapped[UUID | None] = mapped_column(ForeignKey("animals.id"))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    district: Mapped[str] = mapped_column(String(100), index=True)
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    sample_type: Mapped[str] = mapped_column(String(150))
    suspected_disease: Mapped[str | None] = mapped_column(String(150))
    collection_date: Mapped[date | None] = mapped_column(Date)
    laboratory_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="REQUESTED", index=True)
    result: Mapped[str | None] = mapped_column(Text)
    result_date: Mapped[date | None] = mapped_column(Date)
    result_key: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str] = mapped_column(Text, default="")
