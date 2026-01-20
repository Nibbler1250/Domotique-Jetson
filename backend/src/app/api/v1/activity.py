"""Activity log API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.api.v1.auth import get_current_user
from app.core.response import api_response
from app.db.database import get_connection
from app.services import activity_logs as activity_service

router = APIRouter(prefix="/activity", tags=["activity"])


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("", response_model=dict[str, Any])
async def get_activity_logs(
    skip: int = 0,
    limit: int = 50,
    action: str | None = None,
    user_id: int | None = None,
    resource_type: str | None = None,
    current_user: dict = Depends(require_admin),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get activity logs with optional filtering.

    Admin only endpoint.

    Query params:
    - skip: Number of records to skip (pagination)
    - limit: Max records to return (default 50, max 200)
    - action: Filter by action type (e.g., login, device_on)
    - user_id: Filter by user ID
    - resource_type: Filter by resource type (e.g., device, mode)
    """
    if limit > 200:
        limit = 200

    logs = await activity_service.get_activity_logs(
        conn,
        skip=skip,
        limit=limit,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
    )

    # Parse details JSON for each log
    for log in logs:
        if log.get("details"):
            import json
            try:
                log["details"] = json.loads(log["details"])
            except json.JSONDecodeError:
                pass

    return api_response(logs)


@router.get("/summary", response_model=dict[str, Any])
async def get_activity_summary(
    hours: int = 24,
    current_user: dict = Depends(require_admin),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get summary of recent activity.

    Admin only endpoint.

    Query params:
    - hours: Number of hours to look back (default 24, max 168 = 1 week)
    """
    if hours > 168:
        hours = 168

    summary = await activity_service.get_activity_log_summary(conn, hours=hours)
    return api_response(summary)


@router.get("/actions", response_model=dict[str, Any])
async def get_action_types(
    current_user: dict = Depends(require_admin),
) -> dict[str, Any]:
    """Get list of available action types."""
    return api_response({
        "auth": ["login", "logout", "login_failed"],
        "devices": ["device_on", "device_off", "device_set_level", "device_set_color"],
        "modes": ["mode_activate", "mode_create", "mode_update", "mode_delete"],
        "automations": ["automation_toggle", "automation_execute"],
        "config": ["config_export", "config_import"],
        "users": ["user_create", "user_update", "user_delete"],
        "system": ["system_startup", "system_shutdown"],
    })
