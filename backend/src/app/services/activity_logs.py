"""Activity log service for tracking admin actions."""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models.activity_logs import activity_logs


async def log_activity(
    conn: AsyncConnection,
    action: str,
    user_id: int | None = None,
    username: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    resource_name: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    """Log an activity."""
    result = await conn.execute(
        activity_logs.insert().values(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            resource_name=resource_name,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
        ).returning(activity_logs)
    )
    await conn.commit()
    row = result.mappings().first()
    return dict(row) if row else {}


async def get_activity_logs(
    conn: AsyncConnection,
    skip: int = 0,
    limit: int = 50,
    action: str | None = None,
    user_id: int | None = None,
    resource_type: str | None = None,
) -> list[dict[str, Any]]:
    """Get activity logs with optional filtering."""
    query = select(activity_logs).order_by(desc(activity_logs.c.timestamp))

    if action:
        query = query.where(activity_logs.c.action == action)
    if user_id:
        query = query.where(activity_logs.c.user_id == user_id)
    if resource_type:
        query = query.where(activity_logs.c.resource_type == resource_type)

    query = query.offset(skip).limit(limit)

    result = await conn.execute(query)
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def get_activity_log_summary(
    conn: AsyncConnection,
    hours: int = 24,
) -> dict[str, Any]:
    """Get summary of recent activity."""
    from sqlalchemy import func

    # Get counts by action type
    query = select(
        activity_logs.c.action,
        func.count().label("count")
    ).where(
        activity_logs.c.timestamp >= func.datetime('now', f'-{hours} hours')
    ).group_by(activity_logs.c.action)

    result = await conn.execute(query)
    action_counts = {row["action"]: row["count"] for row in result.mappings()}

    # Get total count
    total_query = select(func.count()).select_from(activity_logs).where(
        activity_logs.c.timestamp >= func.datetime('now', f'-{hours} hours')
    )
    total_result = await conn.execute(total_query)
    total_count = total_result.scalar() or 0

    # Get unique users
    users_query = select(func.count(func.distinct(activity_logs.c.user_id))).select_from(activity_logs).where(
        activity_logs.c.timestamp >= func.datetime('now', f'-{hours} hours')
    )
    users_result = await conn.execute(users_query)
    unique_users = users_result.scalar() or 0

    return {
        "period_hours": hours,
        "total_activities": total_count,
        "unique_users": unique_users,
        "by_action": action_counts,
    }


# Pre-defined action types
class ActivityAction:
    """Standard activity action types."""

    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"

    # Devices
    DEVICE_ON = "device_on"
    DEVICE_OFF = "device_off"
    DEVICE_SET_LEVEL = "device_set_level"
    DEVICE_SET_COLOR = "device_set_color"

    # Modes
    MODE_ACTIVATE = "mode_activate"
    MODE_CREATE = "mode_create"
    MODE_UPDATE = "mode_update"
    MODE_DELETE = "mode_delete"

    # Automations
    AUTOMATION_TOGGLE = "automation_toggle"
    AUTOMATION_EXECUTE = "automation_execute"

    # Config
    CONFIG_EXPORT = "config_export"
    CONFIG_IMPORT = "config_import"

    # Users
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

    # System
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
