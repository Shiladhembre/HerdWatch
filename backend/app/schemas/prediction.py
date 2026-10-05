from uuid import UUID
from datetime import datetime
from pydantic import Field, field_validator
from .common import Schema
from app.core.symptom_config import FEATURE_CODES


class DiseaseInput(Schema):
    case_id: UUID | None = None
    symptoms: dict[str, int]

    @field_validator("symptoms", mode="before")
    @classmethod
    def exact_features(cls, v):
        if not isinstance(v, dict) or set(v) != set(FEATURE_CODES):
            raise ValueError("Exactly G01–G18 are required.")
        if any(type(x) is not int or x not in (0, 1) for x in v.values()):
            raise ValueError("Every feature must be integer 0 or 1.")
        return v


class RiskInput(Schema):
    prediction_cutoff: datetime
    features: dict[str, float | str] = Field(min_length=1, max_length=100)
    observed_at: dict[str, datetime]

    @field_validator("prediction_cutoff")
    @classmethod
    def aware_cutoff(cls, v):
        if not v.tzinfo or v.timestamp() > datetime.now().timestamp():
            raise ValueError("Prediction cutoff must be timezone-aware and not in the future.")
        return v


class AssessmentView(Schema):
    suspected_disease: str | None = None
    outbreak_risk: str | None = None
    triage_priority: str | None = None
    confidence: float | None = None
    confidence_calibrated: bool = False
    veterinary_confirmation_required: bool = True
    model_version: str
    disclaimer: str
    reasons: list[str] = Field(default_factory=list)
