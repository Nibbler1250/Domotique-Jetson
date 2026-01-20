"""Device model using SQLAlchemy Core."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Table, Column, Text, text

from app.db.database import metadata


devices = Table(
    "devices",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hubitat_id", Integer, unique=True, nullable=False, index=True),
    Column("name", String(100), nullable=False),
    Column("label", String(100), nullable=True),
    Column("type", String(100), nullable=False),
    Column("room", String(50), nullable=True),
    Column("is_favorite", Boolean, nullable=False, server_default=text("0")),
    Column("is_hidden", Boolean, nullable=False, server_default=text("0")),
    Column("display_order", Integer, nullable=True),
    Column("icon", String(50), nullable=True),
    Column("capabilities", Text, nullable=True),  # JSON string
    # Device state attributes (updated via refresh-states endpoint)
    Column("temperature", Float, nullable=True),
    Column("humidity", Float, nullable=True),
    Column("battery", Integer, nullable=True),
    Column("switch_state", String(20), nullable=True),  # on, off
    Column("level", Integer, nullable=True),  # 0-100
    Column("heating_setpoint", Float, nullable=True),
    Column("cooling_setpoint", Float, nullable=True),
    Column("thermostat_mode", String(20), nullable=True),  # heat, cool, auto, off
    Column("operating_state", String(20), nullable=True),  # heating, cooling, idle
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    Column("updated_at", DateTime(timezone=True), nullable=True, onupdate=datetime.now(timezone.utc)),
)
