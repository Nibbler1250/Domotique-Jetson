"""Modes API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.response import api_response
from app.db.database import get_connection
from app.services import modes as modes_service

router = APIRouter(prefix="/modes", tags=["modes"])


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


class ModeActionSchema(BaseModel):
    """Schema for a mode action."""

    type: str  # device, temperature, delay
    command: str | None = None
    value: Any | None = None
    device_id: int | None = None
    device_type: str | None = None
    rooms: list[str] | None = None
    seconds: int | None = None  # For delay actions


class ModeCreateSchema(BaseModel):
    """Schema for creating a mode."""

    name: str
    label: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    actions: list[ModeActionSchema]


class ModeUpdateSchema(BaseModel):
    """Schema for updating a mode."""

    label: str | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    actions: list[ModeActionSchema] | None = None
    is_enabled: bool | None = None
    display_order: int | None = None


@router.get("", response_model=dict[str, Any])
async def list_modes(
    enabled_only: bool = False,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """List all modes."""
    modes_list = await modes_service.get_all_modes(conn, enabled_only=enabled_only)
    return api_response(modes_list)


@router.get("/active", response_model=dict[str, Any])
async def get_active_mode(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Get the currently active mode."""
    mode = await modes_service.get_active_mode(conn)
    return api_response(mode)


@router.get("/{mode_id}", response_model=dict[str, Any])
async def get_mode(mode_id: int, conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Get a mode by ID."""
    mode = await modes_service.get_mode_by_id(conn, mode_id)
    if not mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mode not found")
    return api_response(mode)


@router.post("", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_mode(
    mode: ModeCreateSchema,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Create a new mode (admin only)."""
    # Check if name already exists
    existing = await modes_service.get_mode_by_name(conn, mode.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mode with name '{mode.name}' already exists",
        )

    actions = [a.model_dump(exclude_none=True) for a in mode.actions]
    created = await modes_service.create_mode(
        conn,
        name=mode.name,
        label=mode.label,
        actions=actions,
        description=mode.description,
        icon=mode.icon,
        color=mode.color,
    )
    return api_response(created)


@router.patch("/{mode_id}", response_model=dict[str, Any])
async def update_mode(
    mode_id: int,
    mode_update: ModeUpdateSchema,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Update a mode."""
    actions = None
    if mode_update.actions is not None:
        actions = [a.model_dump(exclude_none=True) for a in mode_update.actions]

    updated = await modes_service.update_mode(
        conn,
        mode_id=mode_id,
        label=mode_update.label,
        description=mode_update.description,
        icon=mode_update.icon,
        color=mode_update.color,
        actions=actions,
        is_enabled=mode_update.is_enabled,
        display_order=mode_update.display_order,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mode not found")
    return api_response(updated)


@router.delete("/{mode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mode(mode_id: int, conn: AsyncConnection = Depends(get_conn)) -> None:
    """Delete a mode."""
    deleted = await modes_service.delete_mode(conn, mode_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mode not found")


@router.post("/{mode_id}/activate", response_model=dict[str, Any])
async def activate_mode(
    mode_id: int,
    triggered_by: str = "user",
    use_mistral_brain: bool = False,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Activate a mode and execute all its actions.

    Args:
        mode_id: The mode ID to activate
        triggered_by: Source of activation (user, schedule, automation)
        use_mistral_brain: If True, try to execute via Mistral Brain first
    """
    try:
        result = await modes_service.activate_mode(
            conn,
            mode_id=mode_id,
            triggered_by=triggered_by,
            use_mistral_brain=use_mistral_brain,
        )
        return api_response(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate mode: {str(e)}",
        )


@router.post("/deactivate", response_model=dict[str, Any])
async def deactivate_all_modes(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Deactivate all modes (no mode active)."""
    await modes_service.deactivate_all_modes(conn)
    return api_response({"message": "All modes deactivated"})


@router.get("/{mode_id}/executions", response_model=dict[str, Any])
async def get_mode_executions(
    mode_id: int,
    limit: int = 50,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get execution history for a mode."""
    # Verify mode exists
    mode = await modes_service.get_mode_by_id(conn, mode_id)
    if not mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mode not found")

    executions = await modes_service.get_mode_executions(conn, mode_id=mode_id, limit=limit)
    return api_response(executions)


@router.get("/executions/all", response_model=dict[str, Any])
async def get_all_executions(
    limit: int = 50,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get all mode execution history."""
    executions = await modes_service.get_mode_executions(conn, limit=limit)
    return api_response(executions)
