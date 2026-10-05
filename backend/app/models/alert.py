from uuid import UUID
from sqlalchemy import String, Text, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity


class Alert(Entity, Base):
    __tablename__ = "alerts"
    type: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(100), default="Maharashtra")
    district: Mapped[str] = mapped_column(String(100), index=True)
    block: Mapped[str] = mapped_column(String(100), default="")
    village: Mapped[str] = mapped_column(String(150), default="")
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.id"))
    outbreak_id: Mapped[UUID | None] = mapped_column(ForeignKey("outbreaks.id"))
    translations: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class AlertRead(Entity, Base):
    __tablename__ = "alert_reads"
    __table_args__ = (UniqueConstraint("alert_id", "user_id"),)
    alert_id: Mapped[UUID] = mapped_column(ForeignKey("alerts.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=True)
