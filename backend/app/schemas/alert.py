from uuid import UUID
from typing import Literal
from pydantic import Field
from .common import Schema


class AlertCreate(Schema):
    type: Literal[
        "OUTBREAK", "HIGH_MORTALITY", "HIGH_RISK_AREA", "VACCINATION_DUE", "LAB_RESULT", "WEATHER_RISK", "SYSTEM"
    ]
    severity: Literal["INFO", "MEDIUM", "HIGH", "CRITICAL"]
    title: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=3, max_length=5000)
    state: str = Field(default="Maharashtra", max_length=100)
    district: str = Field(min_length=1, max_length=100)
    block: str = Field(default="", max_length=100)
    village: str = Field(default="", max_length=150)
    user_id: UUID | None = None
    case_id: UUID | None = None
    outbreak_id: UUID | None = None
    translations: dict[Literal["en", "hi", "mr"], str] = Field(default_factory=dict)
