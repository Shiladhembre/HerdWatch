from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from .common import Schema


class Filters(Schema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    start_date: date | None = None
    end_date: date | None = None
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    block: str | None = Field(default=None, max_length=100)
    village: str | None = Field(default=None, max_length=150)
    species: str | None = Field(default=None, max_length=30)
    disease: str | None = Field(default=None, max_length=150)
    risk: str | None = Field(default=None, max_length=10)
    status: str | None = Field(default=None, max_length=40)
    search: str | None = Field(default=None, max_length=150)
    sort: Literal["newest", "oldest"] = "newest"

    @model_validator(mode="after")
    def dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date must precede end date.")
        return self
