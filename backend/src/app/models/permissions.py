"""User device permissions model using SQLAlchemy Core."""

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Table, Column, text

from app.db.database import metadata


# User device permissions - which devices each user can control
user_device_permissions = Table(
    "user_device_permissions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("device_id", Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("can_control", Boolean, nullable=False, server_default=text("1")),
    Column("can_view", Boolean, nullable=False, server_default=text("1")),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
)
