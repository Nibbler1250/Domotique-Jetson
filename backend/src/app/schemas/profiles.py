"""Pydantic schemas for profiles."""

from typing import Any

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    """Base profile schema."""

    theme: str = Field(default="system")
    color_scheme: str | None = None
    font_size: str = Field(default="medium")
    contrast: str = Field(default="normal")
    dashboard_layout: dict[str, Any] | None = None
    favorite_devices: list[int] | None = None
    default_room: str | None = None
    show_weather: bool = True
    show_clock: bool = True
    reduce_motion: bool = False
    high_contrast: bool = False
    large_touch_targets: bool = False
    kiosk_auto_dim: bool = True
    kiosk_dim_start: str | None = None
    kiosk_dim_end: str | None = None
    kiosk_dim_brightness: int = Field(default=30, ge=0, le=100)


class ProfileUpdate(BaseModel):
    """Schema for updating a profile."""

    theme: str | None = None
    color_scheme: str | None = None
    font_size: str | None = None
    contrast: str | None = None
    dashboard_layout: dict[str, Any] | None = None
    favorite_devices: list[int] | None = None
    default_room: str | None = None
    show_weather: bool | None = None
    show_clock: bool | None = None
    reduce_motion: bool | None = None
    high_contrast: bool | None = None
    large_touch_targets: bool | None = None
    kiosk_auto_dim: bool | None = None
    kiosk_dim_start: str | None = None
    kiosk_dim_end: str | None = None
    kiosk_dim_brightness: int | None = None


class ProfileResponse(ProfileBase):
    """Profile response schema."""

    id: int
    user_id: int
    created_at: str
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class ThemeInfo(BaseModel):
    """Theme information."""

    id: str
    name: str
    description: str
    preview_colors: dict[str, str]
