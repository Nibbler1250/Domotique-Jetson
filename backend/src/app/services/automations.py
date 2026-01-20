"""Automations service for tracking and managing automation history."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models.automations import alerts, automation_executions, automations

logger = logging.getLogger(__name__)


# ============================================================================
# Automation CRUD
# ============================================================================


async def get_automation_by_id(conn: AsyncConnection, automation_id: int) -> dict[str, Any] | None:
    """Get an automation by ID."""
    result = await conn.execute(select(automations).where(automations.c.id == automation_id))
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("trigger_config"):
        data["trigger_config"] = json.loads(data["trigger_config"])
    return data


async def get_automation_by_name(conn: AsyncConnection, brain_name: str) -> dict[str, Any] | None:
    """Get an automation by Mistral Brain name."""
    result = await conn.execute(
        select(automations).where(automations.c.brain_name == brain_name)
    )
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("trigger_config"):
        data["trigger_config"] = json.loads(data["trigger_config"])
    return data


async def get_all_automations(
    conn: AsyncConnection,
    enabled_only: bool = False,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get all automations."""
    query = select(automations)
    if enabled_only:
        query = query.where(automations.c.is_enabled == True)  # noqa: E712
    query = query.order_by(automations.c.label).limit(limit)

    result = await conn.execute(query)
    automation_list = []
    for row in result.fetchall():
        data = dict(row._mapping)
        if data.get("trigger_config"):
            data["trigger_config"] = json.loads(data["trigger_config"])
        automation_list.append(data)
    return automation_list


async def upsert_automation(
    conn: AsyncConnection,
    brain_name: str,
    label: str,
    description: str | None = None,
    trigger_type: str | None = None,
    trigger_config: dict[str, Any] | None = None,
    actions_count: int = 0,
    is_enabled: bool = True,
) -> dict[str, Any]:
    """Create or update an automation from Mistral Brain data."""
    existing = await get_automation_by_name(conn, brain_name)

    values = {
        "brain_name": brain_name,
        "label": label,
        "description": description,
        "trigger_type": trigger_type,
        "trigger_config": json.dumps(trigger_config) if trigger_config else None,
        "actions_count": actions_count,
        "is_enabled": is_enabled,
    }

    if existing:
        values["updated_at"] = datetime.now(timezone.utc)
        await conn.execute(
            update(automations)
            .where(automations.c.brain_name == brain_name)
            .values(**values)
        )
        await conn.commit()
        return await get_automation_by_name(conn, brain_name)  # type: ignore
    else:
        result = await conn.execute(
            insert(automations).values(**values).returning(automations)
        )
        await conn.commit()
        row = result.fetchone()
        data = dict(row._mapping) if row else {}
        if data.get("trigger_config"):
            data["trigger_config"] = json.loads(data["trigger_config"])
        return data


async def update_automation_status(
    conn: AsyncConnection,
    automation_id: int,
    is_enabled: bool | None = None,
) -> dict[str, Any] | None:
    """Update automation enabled status."""
    update_data: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if is_enabled is not None:
        update_data["is_enabled"] = is_enabled

    result = await conn.execute(
        update(automations)
        .where(automations.c.id == automation_id)
        .values(**update_data)
        .returning(automations)
    )
    await conn.commit()
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("trigger_config"):
        data["trigger_config"] = json.loads(data["trigger_config"])
    return data


async def delete_automation(conn: AsyncConnection, automation_id: int) -> bool:
    """Delete an automation."""
    result = await conn.execute(
        delete(automations).where(automations.c.id == automation_id)
    )
    await conn.commit()
    return result.rowcount > 0


# ============================================================================
# Execution History
# ============================================================================


async def log_execution(
    conn: AsyncConnection,
    brain_name: str,
    success: bool,
    actions_total: int,
    actions_succeeded: int,
    actions_failed: int,
    triggered_by: str | None = None,
    trigger_detail: str | None = None,
    duration_ms: int | None = None,
    error_message: str | None = None,
    error_details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Log an automation execution."""
    # Get automation_id if exists
    automation = await get_automation_by_name(conn, brain_name)
    automation_id = automation["id"] if automation else None

    values = {
        "automation_id": automation_id,
        "brain_name": brain_name,
        "triggered_by": triggered_by,
        "trigger_detail": trigger_detail,
        "success": success,
        "actions_total": actions_total,
        "actions_succeeded": actions_succeeded,
        "actions_failed": actions_failed,
        "duration_ms": duration_ms,
        "error_message": error_message,
        "error_details": json.dumps(error_details) if error_details else None,
    }

    result = await conn.execute(
        insert(automation_executions).values(**values).returning(automation_executions)
    )

    # Update automation stats if it exists
    if automation_id:
        await conn.execute(
            update(automations)
            .where(automations.c.id == automation_id)
            .values(
                last_triggered=datetime.now(timezone.utc),
                last_success=success,
                trigger_count=automations.c.trigger_count + 1,
                success_count=automations.c.success_count + (1 if success else 0),
                failure_count=automations.c.failure_count + (0 if success else 1),
            )
        )

    await conn.commit()

    row = result.fetchone()
    data = dict(row._mapping) if row else {}
    if data.get("error_details"):
        data["error_details"] = json.loads(data["error_details"])
    return data


async def get_executions(
    conn: AsyncConnection,
    automation_id: int | None = None,
    brain_name: str | None = None,
    success_only: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Get automation execution history."""
    query = select(automation_executions).order_by(
        automation_executions.c.executed_at.desc()
    )

    if automation_id:
        query = query.where(automation_executions.c.automation_id == automation_id)
    if brain_name:
        query = query.where(automation_executions.c.brain_name == brain_name)
    if success_only is not None:
        query = query.where(automation_executions.c.success == success_only)

    query = query.limit(limit).offset(offset)

    result = await conn.execute(query)
    executions = []
    for row in result.fetchall():
        data = dict(row._mapping)
        if data.get("error_details"):
            data["error_details"] = json.loads(data["error_details"])
        executions.append(data)
    return executions


async def get_execution_by_id(
    conn: AsyncConnection, execution_id: int
) -> dict[str, Any] | None:
    """Get a single execution by ID."""
    result = await conn.execute(
        select(automation_executions).where(automation_executions.c.id == execution_id)
    )
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("error_details"):
        data["error_details"] = json.loads(data["error_details"])
    return data


async def get_execution_stats(
    conn: AsyncConnection,
    hours: int = 24,
) -> dict[str, Any]:
    """Get execution statistics for the last N hours."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Total executions
    total_result = await conn.execute(
        select(func.count())
        .select_from(automation_executions)
        .where(automation_executions.c.executed_at >= cutoff)
    )
    total = total_result.scalar() or 0

    # Successful executions
    success_result = await conn.execute(
        select(func.count())
        .select_from(automation_executions)
        .where(automation_executions.c.executed_at >= cutoff)
        .where(automation_executions.c.success == True)  # noqa: E712
    )
    successful = success_result.scalar() or 0

    # Failed executions
    failed = total - successful

    return {
        "period_hours": hours,
        "total_executions": total,
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / total * 100) if total > 0 else 100,
    }


# ============================================================================
# Alerts
# ============================================================================


async def create_alert(
    conn: AsyncConnection,
    alert_type: str,
    message: str,
    severity: str = "warning",
    source: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new alert."""
    values = {
        "alert_type": alert_type,
        "severity": severity,
        "source": source,
        "message": message,
        "details": json.dumps(details) if details else None,
    }

    result = await conn.execute(insert(alerts).values(**values).returning(alerts))
    await conn.commit()

    row = result.fetchone()
    data = dict(row._mapping) if row else {}
    if data.get("details"):
        data["details"] = json.loads(data["details"])
    return data


async def get_alerts(
    conn: AsyncConnection,
    unacknowledged_only: bool = False,
    severity: str | None = None,
    alert_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Get alerts."""
    query = select(alerts).order_by(alerts.c.created_at.desc())

    if unacknowledged_only:
        query = query.where(alerts.c.is_acknowledged == False)  # noqa: E712
    if severity:
        query = query.where(alerts.c.severity == severity)
    if alert_type:
        query = query.where(alerts.c.alert_type == alert_type)

    query = query.limit(limit)

    result = await conn.execute(query)
    alert_list = []
    for row in result.fetchall():
        data = dict(row._mapping)
        if data.get("details"):
            data["details"] = json.loads(data["details"])
        alert_list.append(data)
    return alert_list


async def acknowledge_alert(
    conn: AsyncConnection,
    alert_id: int,
    user_id: int,
) -> dict[str, Any] | None:
    """Acknowledge an alert."""
    result = await conn.execute(
        update(alerts)
        .where(alerts.c.id == alert_id)
        .values(
            is_acknowledged=True,
            acknowledged_by=user_id,
            acknowledged_at=datetime.now(timezone.utc),
        )
        .returning(alerts)
    )
    await conn.commit()

    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("details"):
        data["details"] = json.loads(data["details"])
    return data


async def get_alert_counts(conn: AsyncConnection) -> dict[str, int]:
    """Get counts of unacknowledged alerts by severity."""
    result = await conn.execute(
        select(alerts.c.severity, func.count())
        .where(alerts.c.is_acknowledged == False)  # noqa: E712
        .group_by(alerts.c.severity)
    )

    counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
    for row in result.fetchall():
        counts[row[0]] = row[1]

    counts["total"] = sum(counts.values())
    return counts
