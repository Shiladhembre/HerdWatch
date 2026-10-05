from datetime import date
from uuid import UUID
from typing import Literal
from pydantic import Field, field_validator
from .common import LocationInput, Schema, Species, not_future
from app.core.constants import Risk


class OutbreakCreate(LocationInput):
    title: str = Field(min_length=3, max_length=200)
    suspected_disease: str = Field(min_length=2, max_length=150)
    species: Species
    risk_level: Risk = Risk.MEDIUM
    started_on: date
    case_ids: list[UUID] = Field(min_length=1, max_length=100)
    _past = field_validator("started_on")(not_future)


class OutbreakUpdate(Schema):
    status: Literal["SUSPECTED", "INVESTIGATING", "CONFIRMED", "RESOLVED"]
    evidence: str = Field(min_length=10, max_length=5000)
