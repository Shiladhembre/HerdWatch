from uuid import UUID
from pydantic import EmailStr, Field
from typing import Literal
from .common import Schema
from app.core.constants import Role


class UserView(Schema):
    id: UUID
    full_name: str
    email: EmailStr
    mobile: str
    role: Role
    state: str
    district: str
    block: str
    village: str
    preferred_language: str
    is_active: bool
    is_verified: bool


class ProfileUpdate(Schema):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    preferred_language: Literal["en", "mr", "hi"] | None = None


class AdminUserUpdate(Schema):
    role: Role | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    district: str | None = Field(default=None, min_length=1, max_length=100)
