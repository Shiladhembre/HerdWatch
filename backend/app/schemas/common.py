from datetime import date
from uuid import UUID
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Count = Annotated[int, Field(strict=True, ge=0)]
Species = Literal["Cattle", "Buffalo", "Goat", "Sheep", "Pig", "Poultry", "Other"]


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


class LocationInput(Schema):
    state: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)
    block: str = Field(default="", max_length=100)
    village: str = Field(min_length=1, max_length=150)
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)

    @model_validator(mode="after")
    def coordinate_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be supplied together.")
        return self


class Subject(Schema):
    animal_id: UUID | None = None
    herd_id: UUID | None = None

    @model_validator(mode="after")
    def exactly_one_subject(self):
        if bool(self.animal_id) == bool(self.herd_id):
            raise ValueError("Supply exactly one of animal_id or herd_id.")
        return self


class NoteInput(Schema):
    notes: str = Field(min_length=3, max_length=5000)


def not_future(value: date):
    if value > date.today():
        raise ValueError("Date cannot be in the future.")
    return value
