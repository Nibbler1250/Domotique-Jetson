"""Device Pydantic schemas."""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    """Base device schema."""

    name: Annotated[str, Field(min_length=1, max_length=100)]
    label: str | None = None
    type: Annotated[str, Field(min_length=1, max_length=100)]
    room: str | None = None
    is_favorite: bool = False
    is_hidden: bool = False
    display_order: int | None = None
    icon: str | None = None
    capabilities: list[str] | None = None


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""

    hubitat_id: int


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""

    label: str | None = None
    room: str | None = None
    is_favorite: bool | None = None
    is_hidden: bool | None = None
    display_order: int | None = None
    icon: str | None = None


class DeviceResponse(DeviceBase):
    """Schema for device response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    hubitat_id: int
    created_at: datetime


class DeviceWithState(DeviceResponse):
    """Device with current state from MQTT."""

    state: dict[str, Any] = {}
