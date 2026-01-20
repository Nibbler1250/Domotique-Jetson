"""User Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.users import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr | None = None
    display_name: Annotated[str, Field(min_length=1, max_length=100)]
    role: UserRole = UserRole.FAMILY_ADULT
    theme: str | None = None


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: Annotated[str, Field(min_length=4, max_length=100)]

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username contains only alphanumeric and underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores allowed)")
        return v.lower()


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    display_name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    role: UserRole | None = None
    theme: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """Schema for user response (excludes password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None


class UserInDB(UserResponse):
    """Schema for user in database (includes hashed_password)."""

    hashed_password: str
