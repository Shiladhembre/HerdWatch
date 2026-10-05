from uuid import UUID
from pydantic import Field
from .common import LocationInput, Schema, Species


class HerdCreate(LocationInput):
    owner_id: UUID | None = None
    herd_name: str = Field(min_length=1, max_length=150)
    species: Species
    animal_count: int = Field(strict=True, ge=1, le=1_000_000)


class HerdUpdate(Schema):
    herd_name: str | None = Field(default=None, min_length=1, max_length=150)
    animal_count: int | None = Field(default=None, strict=True, ge=1, le=1_000_000)
