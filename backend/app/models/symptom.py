from uuid import UUID
from sqlalchemy import String, ForeignKey, Integer, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity


class CaseSymptom(Entity, Base):
    __tablename__ = "case_symptoms"
    __table_args__ = (
        UniqueConstraint("case_id", "symptom_code"),
        CheckConstraint("symptom_value IN (0,1)", name="binary_value"),
    )
    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id"), index=True)
    symptom_code: Mapped[str] = mapped_column(String(3))
    symptom_value: Mapped[int] = mapped_column(Integer)
