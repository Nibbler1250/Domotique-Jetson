"""User profiles API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.api.v1.auth import get_current_user
from app.core.response import api_response
from app.db.database import get_connection
from app.schemas.profiles import ProfileUpdate
from app.services import profiles as profile_service

router = APIRouter(prefix="/profiles", tags=["profiles"])


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


@router.get("/themes", response_model=dict[str, Any])
async def get_themes() -> dict[str, Any]:
    """Get available themes."""
    themes = await profile_service.get_available_themes()
    return api_response(themes)


@router.get("/me", response_model=dict[str, Any])
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get the current user's profile."""
    profile = await profile_service.get_or_create_profile(conn, current_user["id"])
    return api_response(profile)


@router.patch("/me", response_model=dict[str, Any])
async def update_my_profile(
    profile_update: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Update the current user's profile."""
    # Ensure profile exists
    await profile_service.get_or_create_profile(conn, current_user["id"])

    # Update with non-None values
    update_data = profile_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided",
        )

    updated = await profile_service.update_profile(conn, current_user["id"], **update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )
    return api_response(updated)


@router.get("/{user_id}", response_model=dict[str, Any])
async def get_user_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get a user's profile (admin only, or own profile)."""
    # Allow users to get their own profile, admins can get any
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this profile",
        )

    profile = await profile_service.get_profile_by_user_id(conn, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return api_response(profile)


@router.patch("/{user_id}", response_model=dict[str, Any])
async def update_user_profile(
    user_id: int,
    profile_update: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Update a user's profile (admin only, or own profile)."""
    # Allow users to update their own profile, admins can update any
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile",
        )

    # Ensure profile exists
    await profile_service.get_or_create_profile(conn, user_id)

    update_data = profile_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided",
        )

    updated = await profile_service.update_profile(conn, user_id, **update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )
    return api_response(updated)
