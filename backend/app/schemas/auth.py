from typing import Literal
from pydantic import EmailStr, Field, field_validator
from .common import Schema
from app.core.constants import Role


class RegisterInput(Schema):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    mobile: str = Field(pattern=r"^\+?[1-9]\d{9,14}$")
    password: str = Field(min_length=12, max_length=128)
    role: Role = Role.FARMER
    state: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)
    block: str = Field(default="", max_length=100)
    village: str = Field(default="", max_length=150)
    preferred_language: Literal["en", "mr", "hi"] = "en"

    @field_validator("email")
    @classmethod
    def lowercase(cls, v):
        return str(v).lower()


class LoginInput(Schema):
    identifier: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class RefreshInput(Schema):
    refresh_token: str = Field(min_length=20, max_length=4096)


class ForgotInput(Schema):
    email: EmailStr
