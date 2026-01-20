"""User service for CRUD operations."""

from datetime import datetime, timezone
from typing import Any

import bcrypt
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models.users import UserRole, users
from app.schemas.users import UserCreate, UserUpdate


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


async def get_user_by_id(conn: AsyncConnection, user_id: int) -> dict[str, Any] | None:
    """Get a user by ID."""
    result = await conn.execute(select(users).where(users.c.id == user_id))
    row = result.fetchone()
    return dict(row._mapping) if row else None


async def get_user_by_username(conn: AsyncConnection, username: str) -> dict[str, Any] | None:
    """Get a user by username."""
    result = await conn.execute(select(users).where(users.c.username == username.lower()))
    row = result.fetchone()
    return dict(row._mapping) if row else None


async def get_users(
    conn: AsyncConnection, skip: int = 0, limit: int = 100
) -> list[dict[str, Any]]:
    """Get all users with pagination."""
    result = await conn.execute(select(users).offset(skip).limit(limit))
    return [dict(row._mapping) for row in result.fetchall()]


async def create_user(conn: AsyncConnection, user: UserCreate) -> dict[str, Any]:
    """Create a new user."""
    values = {
        "username": user.username.lower(),
        "email": user.email,
        "hashed_password": hash_password(user.password),
        "display_name": user.display_name,
        "role": user.role.value,
        "theme": user.theme,
    }
    result = await conn.execute(insert(users).values(**values).returning(users))
    await conn.commit()
    row = result.fetchone()
    return dict(row._mapping) if row else {}


async def update_user(
    conn: AsyncConnection, user_id: int, user_update: UserUpdate
) -> dict[str, Any] | None:
    """Update a user."""
    update_data = user_update.model_dump(exclude_unset=True)
    if "role" in update_data and update_data["role"]:
        update_data["role"] = update_data["role"].value
    if not update_data:
        return await get_user_by_id(conn, user_id)

    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await conn.execute(
        update(users).where(users.c.id == user_id).values(**update_data).returning(users)
    )
    await conn.commit()
    row = result.fetchone()
    return dict(row._mapping) if row else None


async def delete_user(conn: AsyncConnection, user_id: int) -> bool:
    """Delete a user."""
    result = await conn.execute(delete(users).where(users.c.id == user_id))
    await conn.commit()
    return result.rowcount > 0


async def update_last_login(conn: AsyncConnection, user_id: int) -> None:
    """Update user's last login timestamp."""
    await conn.execute(
        update(users).where(users.c.id == user_id).values(last_login=datetime.now(timezone.utc))
    )
    await conn.commit()


async def create_default_users(conn: AsyncConnection) -> None:
    """Create default users if they don't exist."""
    defaults = [
        UserCreate(
            username="admin",
            display_name="Administrateur",
            password="admin123",
            role=UserRole.ADMIN,
        ),
        UserCreate(
            username="simon",
            display_name="Simon",
            password="temp123",
            role=UserRole.ADMIN,
            theme="simon",
        ),
        UserCreate(
            username="caroline",
            display_name="Caroline",
            password="temp123",
            role=UserRole.FAMILY_ADULT,
            theme="caroline",
        ),
        UserCreate(
            username="kiosk",
            display_name="Tablette",
            password="kiosk123",
            role=UserRole.KIOSK,
            theme="kiosk",
        ),
    ]

    for user_data in defaults:
        existing = await get_user_by_username(conn, user_data.username)
        if not existing:
            await create_user(conn, user_data)
