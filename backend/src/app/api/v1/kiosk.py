"""Kiosk auto-login API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import get_settings
from app.core.response import api_response
from app.core.security import create_access_token, create_refresh_token
from app.db.database import get_connection
from app.api.v1.auth import set_auth_cookies
from app.schemas.users import UserResponse
from app.services.users import get_user_by_username, update_last_login

router = APIRouter(prefix="/kiosk", tags=["kiosk"])

settings = get_settings()

# Allowed IP addresses for kiosk auto-login (local network)
KIOSK_ALLOWED_IPS = [
    "127.0.0.1",
    "localhost",
    "192.168.1.",  # Local network prefix
]


def is_kiosk_ip_allowed(client_ip: str) -> bool:
    """Check if client IP is allowed for kiosk auto-login."""
    for allowed in KIOSK_ALLOWED_IPS:
        if client_ip.startswith(allowed):
            return True
    return False


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


@router.post("/auto-login", response_model=dict[str, Any])
async def kiosk_auto_login(
    request: Request,
    response: Response,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """
    Auto-login for kiosk devices on local network.
    Only allows connections from trusted IP addresses.
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Also check X-Forwarded-For header (for reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Verify IP is allowed
    if not is_kiosk_ip_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Kiosk auto-login not allowed from this IP: {client_ip}",
        )

    # Get kiosk user
    kiosk_user = await get_user_by_username(conn, "kiosk")
    if not kiosk_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kiosk user not found. Please create a user with username 'kiosk'.",
        )

    if not kiosk_user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kiosk user is disabled",
        )

    # Create tokens
    token_data = {
        "sub": str(kiosk_user["id"]),
        "username": kiosk_user["username"],
        "role": kiosk_user["role"],
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    # Update last login
    await update_last_login(conn, kiosk_user["id"])

    return api_response(
        {
            "user": UserResponse.model_validate(kiosk_user).model_dump(),
            "message": "Kiosk auto-login successful",
            "client_ip": client_ip,
        }
    )
