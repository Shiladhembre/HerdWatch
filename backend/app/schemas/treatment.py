from datetime import date
from uuid import UUID
from pydantic import Field, model_validator, field_validator
from .common import Schema, not_future


class TreatmentCreate(Schema):
    case_id: UUID
    treatment_description: str = Field(min_length=3, max_length=5000)
    medication: str | None = Field(default=None, max_length=300)
    dosage: str | None = Field(default=None, max_length=300)
    started_on: date
    ended_on: date | None = None
    notes: str = Field(default="", max_length=5000)
    _past = field_validator("started_on", "ended_on")(lambda v: not_future(v) if v else v)

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.ended_on and self.ended_on < self.started_on:
            raise ValueError("Treatment end cannot precede start.")
        return self


class TreatmentUpdate(Schema):
    ended_on: date | None = None
    notes: str = Field(min_length=1, max_length=5000)
    _past = field_validator("ended_on")(lambda v: not_future(v) if v else v)
