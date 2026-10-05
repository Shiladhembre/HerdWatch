from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

ImageClass = Literal["foot-and-mouth", "healthy", "lumpy"]


class ImagePrediction(BaseModel):
    predicted_class: ImageClass = Field(alias="class")
    display_name: str
    confidence: float = Field(ge=0, le=1)
    confidence_percent: float = Field(ge=0, le=100)
    low_confidence: bool


class ImageProbabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")
    foot_and_mouth: float = Field(alias="foot-and-mouth", ge=0, le=1)
    healthy: float = Field(ge=0, le=1)
    lumpy: float = Field(ge=0, le=1)


class ImageModelInfo(BaseModel):
    name: str
    classes: list[ImageClass] = Field(min_length=3, max_length=3)


class ImagePredictionResponse(BaseModel):
    success: Literal[True] = True
    prediction: ImagePrediction
    probabilities: ImageProbabilities
    model: ImageModelInfo
    message: str
    disclaimer: str
