"""Activity log database model."""

from sqlalchemy import Column, DateTime, Integer, String, Table, Text, text

from app.db.database import metadata

activity_logs = Table(
    "activity_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False),
    Column("user_id", Integer, nullable=True),  # null for system actions
    Column("username", String(100), nullable=True),
    Column("action", String(50), nullable=False),  # e.g., login, device_control, mode_activate
    Column("resource_type", String(50), nullable=True),  # e.g., device, mode, automation
    Column("resource_id", String(100), nullable=True),  # ID of the affected resource
    Column("resource_name", String(200), nullable=True),  # Name for display
    Column("details", Text, nullable=True),  # JSON with additional details
    Column("ip_address", String(45), nullable=True),
    Column("user_agent", String(500), nullable=True),
)
