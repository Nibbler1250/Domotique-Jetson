"""User model using SQLAlchemy Core."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, Table, Column, text

from app.db.database import metadata


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    FAMILY_ADULT = "family_adult"
    FAMILY_CHILD = "family_child"
    KIOSK = "kiosk"


users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(50), unique=True, nullable=False, index=True),
    Column("email", String(255), unique=True, nullable=True),
    Column("hashed_password", String(255), nullable=False),
    Column("display_name", String(100), nullable=False),
    Column("role", String(20), nullable=False, server_default=text("'family_adult'")),
    Column("is_active", Boolean, nullable=False, server_default=text("1")),
    Column("theme", String(20), nullable=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    Column("updated_at", DateTime(timezone=True), nullable=True, onupdate=datetime.now(timezone.utc)),
    Column("last_login", DateTime(timezone=True), nullable=True),
)
