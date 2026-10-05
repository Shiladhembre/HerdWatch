from uuid import UUID
from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity


class Prediction(Entity, Base):
    __tablename__ = "predictions"
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.id"), index=True)
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str] = mapped_column(String(50))
    input_features: Mapped[dict] = mapped_column(JSONB)
    predicted_class: Mapped[str] = mapped_column(String(150))
    probability: Mapped[float | None] = mapped_column(Float)
