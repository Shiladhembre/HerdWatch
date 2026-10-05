from sqlalchemy import String, Integer, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import Entity


class Location(Entity, Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("source_key"),)
    source_key: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(100))
    block: Mapped[str] = mapped_column(String(100))
    village: Mapped[str] = mapped_column(String(150))
    state_normalized: Mapped[str] = mapped_column(String(100), index=True)
    district_normalized: Mapped[str] = mapped_column(String(100), index=True)
    block_normalized: Mapped[str] = mapped_column(String(100), index=True)
    village_normalized: Mapped[str] = mapped_column(String(150), index=True)
    cattle_population: Mapped[int] = mapped_column(Integer, default=0)
    buffalo_population: Mapped[int] = mapped_column(Integer, default=0)
    sheep_population: Mapped[int] = mapped_column(Integer, default=0)
    goat_population: Mapped[int] = mapped_column(Integer, default=0)
    pig_population: Mapped[int] = mapped_column(Integer, default=0)
    poultry_population: Mapped[int] = mapped_column(Integer, default=0)
    total_livestock: Mapped[int] = mapped_column(Integer, default=0)


class HistoricalObservation(Entity, Base):
    __tablename__ = "historical_observations"
    source_key: Mapped[str] = mapped_column(String(64), unique=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    disease: Mapped[str] = mapped_column(String(150), index=True)
    district: Mapped[str] = mapped_column(String(150), default="", index=True)
    raw_record: Mapped[dict] = mapped_column(JSONB)
    provenance: Mapped[str] = mapped_column(Text)
