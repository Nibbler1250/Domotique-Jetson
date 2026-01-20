"""User API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.response import api_response
from app.db.database import get_connection
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.services import users as user_service

router = APIRouter(prefix="/users", tags=["users"])


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


@router.get("", response_model=dict[str, Any])
async def list_users(
    skip: int = 0, limit: int = 100, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """List all users."""
    users = await user_service.get_users(conn, skip=skip, limit=limit)
    return api_response([UserResponse.model_validate(u).model_dump() for u in users])


@router.get("/{user_id}", response_model=dict[str, Any])
async def get_user(user_id: int, conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Get a user by ID."""
    user = await user_service.get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return api_response(UserResponse.model_validate(user).model_dump())


@router.post("", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Create a new user."""
    existing = await user_service.get_user_by_username(conn, user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    created = await user_service.create_user(conn, user)
    return api_response(UserResponse.model_validate(created).model_dump())


@router.patch("/{user_id}", response_model=dict[str, Any])
async def update_user(
    user_id: int, user_update: UserUpdate, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Update a user."""
    updated = await user_service.update_user(conn, user_id, user_update)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return api_response(UserResponse.model_validate(updated).model_dump())


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, conn: AsyncConnection = Depends(get_conn)) -> None:
    """Delete a user."""
    deleted = await user_service.delete_user(conn, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
