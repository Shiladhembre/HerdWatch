from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, String, ForeignKey, func, Float
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry


class Entity:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Located:
    state: Mapped[str] = mapped_column(String(100), default="Maharashtra")
    district: Mapped[str] = mapped_column(String(100), index=True)
    block: Mapped[str] = mapped_column(String(100), default="", index=True)
    village: Mapped[str] = mapped_column(String(150), index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    geom: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326, spatial_index=True))


class Attributed:
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
