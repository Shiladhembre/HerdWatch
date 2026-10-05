from datetime import date, datetime
from uuid import UUID
from pydantic import Field, model_validator, field_validator
from .common import Subject, LocationInput, Schema, Species, not_future
from app.core.constants import Severity, CaseStatus
from app.core.symptom_config import FEATURE_CODES


class CaseCreate(Subject, LocationInput):
    species: Species
    symptom_started_on: date
    affected_count: int = Field(strict=True, ge=1, le=1_000_000)
    death_count: int = Field(default=0, strict=True, ge=0)
    observed_symptoms: str = Field(default="", max_length=5000)
    symptoms: dict[str, int] = Field(default_factory=dict)
    severity: Severity = Severity.ROUTINE
    notes: str = Field(default="", max_length=5000)
    created_offline_at: datetime | None = None
    _past = field_validator("symptom_started_on")(not_future)

    @field_validator("symptoms", mode="before")
    @classmethod
    def valid_features(cls, v):
        if not isinstance(v, dict) or any(
            k not in FEATURE_CODES or type(x) is not int or x not in (0, 1) for k, x in v.items()
        ):
            raise ValueError("Symptoms must use G01–G18 with integer 0/1 values.")
        return v

    @model_validator(mode="after")
    def valid_counts(self):
        if self.death_count > self.affected_count:
            raise ValueError("Death count cannot exceed affected count.")
        if self.created_offline_at and (
            not self.created_offline_at.tzinfo or self.created_offline_at.timestamp() > datetime.now().timestamp() + 300
        ):
            raise ValueError("Offline timestamp must be timezone-aware and not in the future.")
        return self


class CaseUpdate(Schema):
    notes: str | None = Field(default=None, max_length=5000)
    observed_symptoms: str | None = Field(default=None, max_length=5000)
    affected_count: int | None = Field(default=None, strict=True, ge=1)
    death_count: int | None = Field(default=None, strict=True, ge=0)
    severity: Severity | None = None
    status: CaseStatus | None = None
    clinical_assessment: str | None = Field(default=None, min_length=3, max_length=5000)


class AssignInput(Schema):
    veterinarian_id: UUID


class SyncRecord(Schema):
    client_record_id: str = Field(min_length=8, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    created_offline_at: datetime
    payload: CaseCreate


class SyncInput(Schema):
    records: list[SyncRecord] = Field(min_length=1, max_length=50)
