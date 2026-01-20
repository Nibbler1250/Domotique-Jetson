"""Device permissions API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.response import api_response
from app.db.database import get_connection
from app.services import permissions as permission_service
from app.services import users as user_service

router = APIRouter(prefix="/permissions", tags=["permissions"])


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


class PermissionGrant(BaseModel):
    """Request to grant device permission."""

    device_id: int
    can_control: bool = True
    can_view: bool = True


class BulkPermissionGrant(BaseModel):
    """Request to set all device permissions for a user."""

    device_ids: list[int]
    can_control: bool = True


@router.get("/user/{user_id}", response_model=dict[str, Any])
async def get_user_permissions(
    user_id: int, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Get all device permissions for a user."""
    # Verify user exists
    user = await user_service.get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    permissions = await permission_service.get_user_permissions(conn, user_id)
    device_ids = await permission_service.get_user_device_ids(conn, user_id)

    return api_response({
        "user_id": user_id,
        "username": user["username"],
        "role": user["role"],
        "permissions": permissions,
        "device_ids": device_ids,
    })


@router.get("/user/{user_id}/devices", response_model=dict[str, Any])
async def get_user_device_ids(
    user_id: int, control_only: bool = False, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Get list of device IDs a user can access."""
    device_ids = await permission_service.get_user_device_ids(conn, user_id, control_only)
    return api_response(device_ids)


@router.get("/check/{user_id}/{device_id}", response_model=dict[str, Any])
async def check_permission(
    user_id: int, device_id: int, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Check if a user can control/view a specific device."""
    user = await user_service.get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    can_control = await permission_service.can_user_control_device(
        conn, user_id, device_id, user["role"]
    )
    can_view = await permission_service.can_user_view_device(
        conn, user_id, device_id, user["role"]
    )

    return api_response({
        "user_id": user_id,
        "device_id": device_id,
        "can_control": can_control,
        "can_view": can_view,
    })


@router.post("/user/{user_id}/grant", response_model=dict[str, Any])
async def grant_permission(
    user_id: int, grant: PermissionGrant, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Grant a user permission to a device."""
    # Verify user exists
    user = await user_service.get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    permission = await permission_service.grant_device_permission(
        conn, user_id, grant.device_id, grant.can_control, grant.can_view
    )
    return api_response(permission)


@router.post("/user/{user_id}/bulk", response_model=dict[str, Any])
async def set_bulk_permissions(
    user_id: int, bulk: BulkPermissionGrant, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Set all device permissions for a user (replaces existing)."""
    # Verify user exists
    user = await user_service.get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    permissions = await permission_service.set_user_device_permissions(
        conn, user_id, bulk.device_ids, bulk.can_control
    )
    return api_response({
        "user_id": user_id,
        "permissions_count": len(permissions),
        "permissions": permissions,
    })


@router.delete("/user/{user_id}/device/{device_id}", response_model=dict[str, Any])
async def revoke_permission(
    user_id: int, device_id: int, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Revoke a user's permission to a device."""
    revoked = await permission_service.revoke_device_permission(conn, user_id, device_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
        )
    return api_response({"revoked": True, "user_id": user_id, "device_id": device_id})
