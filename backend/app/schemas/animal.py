from datetime import date
from uuid import UUID
from typing import Literal
from pydantic import Field, field_validator
from .common import LocationInput, Schema, Species, not_future


class AnimalCreate(LocationInput):
    owner_id: UUID | None = None
    animal_tag: str = Field(min_length=1, max_length=80)
    species: Species
    breed: str = Field(default="", max_length=100)
    sex: Literal["Female", "Male", "Unknown"] = "Unknown"
    date_of_birth: date | None = None
    approximate_age: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    pregnancy_status: Literal["Unknown", "Pregnant", "Not pregnant", "Not applicable"] = "Unknown"
    health_status: Literal["Healthy", "Needs review"] = "Needs review"

    @field_validator("date_of_birth")
    @classmethod
    def valid_birth(cls, v):
        return not_future(v) if v else v


class AnimalUpdate(Schema):
    breed: str | None = Field(default=None, max_length=100)
    approximate_age: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    health_status: Literal["Healthy", "Needs review"] | None = None
    pregnancy_status: Literal["Unknown", "Pregnant", "Not pregnant", "Not applicable"] | None = None


class AnimalRecordInput(Schema):
    record_type: Literal["Health record", "Note"] = "Note"
    recorded_on: date
    notes: str = Field(min_length=1, max_length=5000)
    _past = field_validator("recorded_on")(not_future)
