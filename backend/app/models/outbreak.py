from uuid import UUID
from datetime import date
from sqlalchemy import String, ForeignKey, Date, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity, Located, Attributed


class Outbreak(Entity, Located, Attributed, Base):
    __tablename__ = "outbreaks"
    title: Mapped[str] = mapped_column(String(200))
    suspected_disease: Mapped[str] = mapped_column(String(150), index=True)
    species: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="SUSPECTED", index=True)
    risk_level: Mapped[str] = mapped_column(String(10), default="MEDIUM")
    started_on: Mapped[date] = mapped_column(Date)
    confirmed_on: Mapped[date | None] = mapped_column(Date)
    confirmed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    evidence: Mapped[str | None] = mapped_column(Text)


class OutbreakCase(Entity, Base):
    __tablename__ = "outbreak_cases"
    __table_args__ = (UniqueConstraint("outbreak_id", "case_id"),)
    outbreak_id: Mapped[UUID] = mapped_column(ForeignKey("outbreaks.id"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id"), index=True)
