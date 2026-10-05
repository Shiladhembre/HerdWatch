from datetime import date
from uuid import UUID
from pydantic import Field, field_validator
from .common import Schema, not_future
from app.core.constants import LabStatus


class LabCreate(Schema):
    case_id: UUID
    sample_type: str = Field(min_length=2, max_length=150)
    laboratory_name: str = Field(min_length=2, max_length=200)
    collection_date: date | None = None
    notes: str = Field(default="", max_length=5000)
    _past = field_validator("collection_date")(lambda v: not_future(v) if v else v)


class LabUpdate(Schema):
    status: LabStatus
    collection_date: date | None = None
    sample_type: str | None = Field(default=None, min_length=2, max_length=150)
    notes: str = Field(default="", max_length=5000)
    _past = field_validator("collection_date")(lambda v: not_future(v) if v else v)


class LabResult(Schema):
    result: str = Field(min_length=5, max_length=10000)
    result_date: date
    _past = field_validator("result_date")(not_future)
