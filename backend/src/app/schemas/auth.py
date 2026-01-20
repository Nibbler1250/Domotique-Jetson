"""Authentication Pydantic schemas."""

from typing import Annotated

from pydantic import BaseModel, Field

from app.models.users import UserRole


class LoginRequest(BaseModel):
    """Login request schema."""

    username: Annotated[str, Field(min_length=1, max_length=50)]
    password: Annotated[str, Field(min_length=1, max_length=100)]


class TokenResponse(BaseModel):
    """Token response schema (for JSON body responses)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: str  # user_id
    username: str
    role: UserRole
    exp: int
    type: str
