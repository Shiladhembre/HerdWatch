from uuid import UUID
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity


class AuditLog(Entity, Base):
    __tablename__ = "audit_logs"
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[UUID] = mapped_column(index=True)
    details: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
