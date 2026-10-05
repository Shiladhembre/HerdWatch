from datetime import date
from pydantic import Field, model_validator, field_validator
from .common import Subject, Schema, not_future


class VaccinationCreate(Subject):
    vaccine_name: str = Field(min_length=1, max_length=150)
    disease_target: str = Field(min_length=1, max_length=150)
    dose_number: int = Field(strict=True, ge=1, le=100)
    administered_on: date
    next_due_on: date | None = None
    batch_number: str | None = Field(default=None, max_length=100)
    notes: str = Field(default="", max_length=5000)
    _past = field_validator("administered_on")(not_future)

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.next_due_on and self.next_due_on < self.administered_on:
            raise ValueError("Next due date cannot precede administration.")
        return self


class VaccinationUpdate(Schema):
    next_due_on: date | None = None
    batch_number: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=5000)
