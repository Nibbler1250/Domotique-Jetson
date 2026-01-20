"""User profiles service for themes and preferences."""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models.profiles import profiles


async def get_profile_by_user_id(conn: AsyncConnection, user_id: int) -> dict[str, Any] | None:
    """Get a user's profile by user ID."""
    result = await conn.execute(select(profiles).where(profiles.c.user_id == user_id))
    row = result.mappings().first()
    if row:
        profile = dict(row)
        # Parse JSON fields
        if profile.get("dashboard_layout"):
            profile["dashboard_layout"] = json.loads(profile["dashboard_layout"])
        if profile.get("favorite_devices"):
            profile["favorite_devices"] = json.loads(profile["favorite_devices"])
        return profile
    return None


async def create_profile(conn: AsyncConnection, user_id: int, **kwargs: Any) -> dict[str, Any]:
    """Create a profile for a user."""
    data = {"user_id": user_id, **kwargs}

    # Serialize JSON fields
    if "dashboard_layout" in data and data["dashboard_layout"] is not None:
        data["dashboard_layout"] = json.dumps(data["dashboard_layout"])
    if "favorite_devices" in data and data["favorite_devices"] is not None:
        data["favorite_devices"] = json.dumps(data["favorite_devices"])

    result = await conn.execute(profiles.insert().values(**data).returning(profiles))
    await conn.commit()
    row = result.mappings().first()
    if row:
        profile = dict(row)
        # Parse JSON fields back
        if profile.get("dashboard_layout"):
            profile["dashboard_layout"] = json.loads(profile["dashboard_layout"])
        if profile.get("favorite_devices"):
            profile["favorite_devices"] = json.loads(profile["favorite_devices"])
        return profile
    return data


async def update_profile(
    conn: AsyncConnection, user_id: int, **kwargs: Any
) -> dict[str, Any] | None:
    """Update a user's profile."""
    # Serialize JSON fields if present
    if "dashboard_layout" in kwargs and kwargs["dashboard_layout"] is not None:
        kwargs["dashboard_layout"] = json.dumps(kwargs["dashboard_layout"])
    if "favorite_devices" in kwargs and kwargs["favorite_devices"] is not None:
        kwargs["favorite_devices"] = json.dumps(kwargs["favorite_devices"])

    result = await conn.execute(
        profiles.update()
        .where(profiles.c.user_id == user_id)
        .values(**kwargs)
        .returning(profiles)
    )
    await conn.commit()
    row = result.mappings().first()
    if row:
        profile = dict(row)
        # Parse JSON fields back
        if profile.get("dashboard_layout"):
            profile["dashboard_layout"] = json.loads(profile["dashboard_layout"])
        if profile.get("favorite_devices"):
            profile["favorite_devices"] = json.loads(profile["favorite_devices"])
        return profile
    return None


async def get_or_create_profile(conn: AsyncConnection, user_id: int) -> dict[str, Any]:
    """Get a user's profile, creating one with defaults if it doesn't exist."""
    profile = await get_profile_by_user_id(conn, user_id)
    if profile:
        return profile
    return await create_profile(conn, user_id)


async def delete_profile(conn: AsyncConnection, user_id: int) -> bool:
    """Delete a user's profile."""
    result = await conn.execute(profiles.delete().where(profiles.c.user_id == user_id))
    await conn.commit()
    return result.rowcount > 0


async def get_available_themes() -> list[dict[str, Any]]:
    """Get list of available themes with metadata."""
    return [
        {
            "id": "system",
            "name": "Système",
            "description": "Suit le thème du système",
            "preview_colors": {"primary": "#3b82f6", "bg": "#ffffff", "surface": "#f3f4f6"},
        },
        {
            "id": "light",
            "name": "Clair",
            "description": "Thème clair classique",
            "preview_colors": {"primary": "#3b82f6", "bg": "#ffffff", "surface": "#f3f4f6"},
        },
        {
            "id": "dark",
            "name": "Sombre",
            "description": "Thème sombre pour économiser les yeux",
            "preview_colors": {"primary": "#60a5fa", "bg": "#0f172a", "surface": "#1e293b"},
        },
        {
            "id": "simon",
            "name": "Simon",
            "description": "Bleu tech moderne",
            "preview_colors": {"primary": "#0ea5e9", "bg": "#0c1929", "surface": "#1a2e44"},
        },
        {
            "id": "caroline",
            "name": "Caroline",
            "description": "Tons chauds apaisants",
            "preview_colors": {"primary": "#f472b6", "bg": "#fdf2f8", "surface": "#fce7f3"},
        },
        {
            "id": "kids",
            "name": "Enfants",
            "description": "Coloré et amusant",
            "preview_colors": {"primary": "#a855f7", "bg": "#faf5ff", "surface": "#f3e8ff"},
        },
        {
            "id": "kiosk",
            "name": "Kiosk",
            "description": "Optimisé pour tablette murale",
            "preview_colors": {"primary": "#10b981", "bg": "#000000", "surface": "#111827"},
        },
    ]
