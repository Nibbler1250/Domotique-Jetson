"""Authentication API endpoints."""

from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.response import api_response
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.db.database import get_connection
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.users import UserResponse
from app.services.users import (
    get_user_by_id,
    get_user_by_username,
    update_last_login,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly cookies for JWT tokens."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="none" if not False else "lax",  # none for cross-origin in dev
        max_age=30 * 60,  # 30 minutes
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="none" if not False else "lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear auth cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.post("/login", response_model=dict[str, Any])
async def login(
    login_data: LoginRequest,
    response: Response,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Authenticate user and return JWT tokens in httpOnly cookies."""
    user = await get_user_by_username(conn, login_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create tokens
    token_data = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    # Update last login
    await update_last_login(conn, user["id"])

    return api_response(
        {
            "user": UserResponse.model_validate(user).model_dump(),
            "message": "Login successful",
        }
    )


@router.post("/refresh", response_model=dict[str, Any])
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Refresh access token using refresh token from cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    payload = decode_token(refresh_token)
    if not payload or not verify_token_type(payload, "refresh"):
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify user still exists and is active
    user_id = int(payload["sub"])
    user = await get_user_by_id(conn, user_id)
    if not user or not user["is_active"]:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    # Create new tokens
    token_data = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Set new cookies
    set_auth_cookies(response, new_access_token, new_refresh_token)

    return api_response({"message": "Token refreshed successfully"})


@router.post("/logout")
async def logout(response: Response) -> dict[str, Any]:
    """Logout user by clearing auth cookies."""
    clear_auth_cookies(response)
    return api_response({"message": "Logged out successfully"})


@router.get("/me", response_model=dict[str, Any])
async def get_current_user(
    access_token: str | None = Cookie(default=None),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get current authenticated user from access token cookie."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(access_token)
    if not payload or not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = int(payload["sub"])
    user = await get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return api_response(UserResponse.model_validate(user).model_dump())
