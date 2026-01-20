"""Automations API endpoints for monitoring and managing automations."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.response import api_response
from app.db.database import get_connection
from app.services import automations as automation_service
from app.services.mistral_brain import get_mistral_brain_service

router = APIRouter(prefix="/automations", tags=["automations"])


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


class AutomationUpdateSchema(BaseModel):
    """Schema for updating an automation."""

    is_enabled: bool | None = None


class AlertAcknowledgeSchema(BaseModel):
    """Schema for acknowledging an alert."""

    user_id: int


# ============================================================================
# Automations
# ============================================================================


@router.get("", response_model=dict[str, Any])
async def list_automations(
    enabled_only: bool = False,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """List all automations."""
    automations = await automation_service.get_all_automations(
        conn, enabled_only=enabled_only
    )
    return api_response(automations)


@router.get("/sync", response_model=dict[str, Any])
async def sync_from_brain(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Sync automations from Mistral Brain.

    This fetches the current automation list from Mistral Brain
    and updates the local database.
    """
    brain = get_mistral_brain_service()

    try:
        brain_automations = await brain.get_automations()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Mistral Brain: {str(e)}",
        )

    synced = []
    for ba in brain_automations:
        automation = await automation_service.upsert_automation(
            conn,
            brain_name=ba.get("name", "unknown"),
            label=ba.get("label", ba.get("name", "Unknown")),
            description=ba.get("description"),
            trigger_type=ba.get("trigger", {}).get("type"),
            trigger_config=ba.get("trigger"),
            actions_count=len(ba.get("actions", [])),
            is_enabled=ba.get("enabled", True),
        )
        synced.append(automation)

    return api_response({"synced": len(synced), "automations": synced})


@router.get("/{automation_id}", response_model=dict[str, Any])
async def get_automation(
    automation_id: int,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get an automation by ID."""
    automation = await automation_service.get_automation_by_id(conn, automation_id)
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found",
        )
    return api_response(automation)


@router.get("/{automation_id}/details", response_model=dict[str, Any])
async def get_automation_details(
    automation_id: int,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get full automation details from Mistral Brain, including actions."""
    # Get local automation first to get the brain_name
    automation = await automation_service.get_automation_by_id(conn, automation_id)
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found",
        )

    # Fetch full details from Mistral Brain
    brain = get_mistral_brain_service()
    try:
        brain_details = await brain.get_automation_by_name(automation["brain_name"])
        if brain_details:
            # Merge local data with brain details
            return api_response({
                **automation,
                "actions": brain_details.get("actions", []),
                "trigger": brain_details.get("trigger", {}),
                "conditions": brain_details.get("conditions", []),
            })
        else:
            return api_response(automation)
    except Exception as e:
        # Return local data if Brain is unavailable
        return api_response({
            **automation,
            "actions": [],
            "error": f"Could not fetch from Brain: {str(e)}",
        })


@router.patch("/{automation_id}", response_model=dict[str, Any])
async def update_automation(
    automation_id: int,
    update_data: AutomationUpdateSchema,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Update an automation (enable/disable)."""
    updated = await automation_service.update_automation_status(
        conn,
        automation_id=automation_id,
        is_enabled=update_data.is_enabled,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found",
        )
    return api_response(updated)


@router.post("/{automation_id}/trigger", response_model=dict[str, Any])
async def trigger_automation(
    automation_id: int,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Manually trigger an automation via Mistral Brain."""
    automation = await automation_service.get_automation_by_id(conn, automation_id)
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found",
        )

    if not automation.get("is_enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automation is disabled",
        )

    brain = get_mistral_brain_service()

    try:
        result = await brain.execute_automation(automation["brain_name"])

        # Log the execution
        await automation_service.log_execution(
            conn,
            brain_name=automation["brain_name"],
            success=result.get("success", True),
            actions_total=result.get("actions_total", 0),
            actions_succeeded=result.get("actions_succeeded", 0),
            actions_failed=result.get("actions_failed", 0),
            triggered_by="user",
            trigger_detail="Manual trigger via API",
        )

        return api_response(result)
    except Exception as e:
        # Log failed execution
        await automation_service.log_execution(
            conn,
            brain_name=automation["brain_name"],
            success=False,
            actions_total=0,
            actions_succeeded=0,
            actions_failed=0,
            triggered_by="user",
            trigger_detail="Manual trigger via API",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to trigger automation: {str(e)}",
        )


# ============================================================================
# Execution History
# ============================================================================


@router.get("/executions/all", response_model=dict[str, Any])
async def list_all_executions(
    limit: int = 50,
    offset: int = 0,
    success_only: bool | None = None,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """List all automation executions."""
    executions = await automation_service.get_executions(
        conn,
        success_only=success_only,
        limit=limit,
        offset=offset,
    )
    return api_response(executions)


@router.get("/executions/stats", response_model=dict[str, Any])
async def get_execution_stats(
    hours: int = 24,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get execution statistics for the last N hours."""
    stats = await automation_service.get_execution_stats(conn, hours=hours)
    return api_response(stats)


@router.get("/{automation_id}/executions", response_model=dict[str, Any])
async def list_automation_executions(
    automation_id: int,
    limit: int = 50,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """List executions for a specific automation."""
    # Verify automation exists
    automation = await automation_service.get_automation_by_id(conn, automation_id)
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found",
        )

    executions = await automation_service.get_executions(
        conn,
        automation_id=automation_id,
        limit=limit,
    )
    return api_response(executions)


@router.get("/executions/{execution_id}", response_model=dict[str, Any])
async def get_execution(
    execution_id: int,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get a single execution by ID."""
    execution = await automation_service.get_execution_by_id(conn, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    return api_response(execution)


# ============================================================================
# Alerts
# ============================================================================


@router.get("/alerts/all", response_model=dict[str, Any])
async def list_alerts(
    unacknowledged_only: bool = False,
    severity: str | None = None,
    limit: int = 50,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """List alerts."""
    alert_list = await automation_service.get_alerts(
        conn,
        unacknowledged_only=unacknowledged_only,
        severity=severity,
        limit=limit,
    )
    return api_response(alert_list)


@router.get("/alerts/counts", response_model=dict[str, Any])
async def get_alert_counts(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Get counts of unacknowledged alerts by severity."""
    counts = await automation_service.get_alert_counts(conn)
    return api_response(counts)


@router.post("/alerts/{alert_id}/acknowledge", response_model=dict[str, Any])
async def acknowledge_alert(
    alert_id: int,
    data: AlertAcknowledgeSchema,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Acknowledge an alert."""
    alert = await automation_service.acknowledge_alert(
        conn,
        alert_id=alert_id,
        user_id=data.user_id,
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return api_response(alert)
