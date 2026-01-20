"""Device permissions service for user access control."""

from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models.permissions import user_device_permissions
from app.models.users import UserRole


async def get_user_permissions(conn: AsyncConnection, user_id: int) -> list[dict[str, Any]]:
    """Get all device permissions for a user."""
    result = await conn.execute(
        select(user_device_permissions).where(user_device_permissions.c.user_id == user_id)
    )
    return [dict(row._mapping) for row in result.fetchall()]


async def get_user_device_ids(
    conn: AsyncConnection, user_id: int, control_only: bool = False
) -> list[int]:
    """Get list of device IDs a user can access.

    Args:
        user_id: User ID
        control_only: If True, only return devices user can control (not just view)
    """
    query = select(user_device_permissions.c.device_id).where(
        user_device_permissions.c.user_id == user_id
    )
    if control_only:
        query = query.where(user_device_permissions.c.can_control == True)  # noqa: E712
    else:
        query = query.where(user_device_permissions.c.can_view == True)  # noqa: E712

    result = await conn.execute(query)
    return [row[0] for row in result.fetchall()]


async def can_user_control_device(
    conn: AsyncConnection, user_id: int, device_id: int, user_role: str
) -> bool:
    """Check if a user can control a specific device.

    Admin and family_adult can control all devices.
    Family_child can only control devices explicitly granted.
    Kiosk cannot control any devices.
    """
    # Admin and adults can control everything
    if user_role in (UserRole.ADMIN.value, UserRole.FAMILY_ADULT.value):
        return True

    # Kiosk cannot control anything
    if user_role == UserRole.KIOSK.value:
        return False

    # Check explicit permission for children
    result = await conn.execute(
        select(user_device_permissions.c.can_control).where(
            (user_device_permissions.c.user_id == user_id)
            & (user_device_permissions.c.device_id == device_id)
        )
    )
    row = result.fetchone()
    return bool(row and row[0])


async def can_user_view_device(
    conn: AsyncConnection, user_id: int, device_id: int, user_role: str
) -> bool:
    """Check if a user can view a specific device.

    Admin, family_adult, and kiosk can view all devices.
    Family_child can only view devices explicitly granted.
    """
    # Admin, adults, and kiosk can view everything
    if user_role in (UserRole.ADMIN.value, UserRole.FAMILY_ADULT.value, UserRole.KIOSK.value):
        return True

    # Check explicit permission for children
    result = await conn.execute(
        select(user_device_permissions.c.can_view).where(
            (user_device_permissions.c.user_id == user_id)
            & (user_device_permissions.c.device_id == device_id)
        )
    )
    row = result.fetchone()
    return bool(row and row[0])


async def grant_device_permission(
    conn: AsyncConnection,
    user_id: int,
    device_id: int,
    can_control: bool = True,
    can_view: bool = True,
) -> dict[str, Any]:
    """Grant a user permission to a device."""
    # Check if permission already exists
    existing = await conn.execute(
        select(user_device_permissions).where(
            (user_device_permissions.c.user_id == user_id)
            & (user_device_permissions.c.device_id == device_id)
        )
    )
    if existing.fetchone():
        # Update existing
        from sqlalchemy import update

        await conn.execute(
            update(user_device_permissions)
            .where(
                (user_device_permissions.c.user_id == user_id)
                & (user_device_permissions.c.device_id == device_id)
            )
            .values(can_control=can_control, can_view=can_view)
        )
    else:
        # Insert new
        await conn.execute(
            insert(user_device_permissions).values(
                user_id=user_id,
                device_id=device_id,
                can_control=can_control,
                can_view=can_view,
            )
        )
    await conn.commit()

    return {
        "user_id": user_id,
        "device_id": device_id,
        "can_control": can_control,
        "can_view": can_view,
    }


async def revoke_device_permission(
    conn: AsyncConnection, user_id: int, device_id: int
) -> bool:
    """Revoke a user's permission to a device."""
    result = await conn.execute(
        delete(user_device_permissions).where(
            (user_device_permissions.c.user_id == user_id)
            & (user_device_permissions.c.device_id == device_id)
        )
    )
    await conn.commit()
    return result.rowcount > 0


async def set_user_device_permissions(
    conn: AsyncConnection, user_id: int, device_ids: list[int], can_control: bool = True
) -> list[dict[str, Any]]:
    """Set the complete list of devices a user can access.

    This replaces all existing permissions for the user.
    """
    # Remove all existing permissions
    await conn.execute(
        delete(user_device_permissions).where(user_device_permissions.c.user_id == user_id)
    )

    # Add new permissions
    permissions = []
    for device_id in device_ids:
        await conn.execute(
            insert(user_device_permissions).values(
                user_id=user_id,
                device_id=device_id,
                can_control=can_control,
                can_view=True,
            )
        )
        permissions.append({
            "user_id": user_id,
            "device_id": device_id,
            "can_control": can_control,
            "can_view": True,
        })

    await conn.commit()
    return permissions
