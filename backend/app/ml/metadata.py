from pydantic import BaseModel, ConfigDict, Field


class ModelContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    version: str
    schema_version: int = Field(default=1, ge=1, le=1)
    trained_at: str | None = None
    features: list[str]
    verified: bool = False
    calibrated: bool = False
    sha256: str | None = None
    feature_artifact_sha256: str | None = None
    label_encoder_sha256: str | None = None
    sklearn_version: str | None = None
    classes: list[str] = Field(default_factory=list)
    triage_priorities: dict[str, str] = Field(default_factory=dict)
    feature_types: dict[str, str] = Field(default_factory=dict)
    pre_outbreak_features: list[str] = Field(default_factory=list)
    maximum_feature_age_days: int = Field(default=3650, ge=1)
