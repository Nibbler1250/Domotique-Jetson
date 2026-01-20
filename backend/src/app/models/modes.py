"""Modes model using SQLAlchemy Core.

Modes are predefined automation sequences that can execute multiple actions.
Examples: Mode Nuit, Mode Matin, Mode Souper, J'ai frette
"""

from sqlalchemy import Boolean, DateTime, Integer, String, Table, Column, Text, text

from app.db.database import metadata


# Modes table - predefined automation sequences
modes = Table(
    "modes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(50), unique=True, nullable=False, index=True),
    Column("label", String(100), nullable=False),
    Column("description", String(255), nullable=True),
    Column("icon", String(50), nullable=True),
    Column("color", String(20), nullable=True),  # For UI display
    Column("actions", Text, nullable=False),  # JSON array of actions
    Column("is_active", Boolean, nullable=False, server_default=text("0")),  # Currently active
    Column("is_enabled", Boolean, nullable=False, server_default=text("1")),  # Can be activated
    Column("display_order", Integer, nullable=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("last_activated", DateTime(timezone=True), nullable=True),
)


# Mode execution log
mode_executions = Table(
    "mode_executions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("mode_id", Integer, nullable=False, index=True),
    Column("mode_name", String(50), nullable=False),
    Column("triggered_by", String(50), nullable=True),  # user, schedule, automation
    Column("user_id", Integer, nullable=True),
    Column("success", Boolean, nullable=False),
    Column("actions_total", Integer, nullable=False),
    Column("actions_succeeded", Integer, nullable=False),
    Column("actions_failed", Integer, nullable=False),
    Column("error_details", Text, nullable=True),  # JSON array of errors
    Column(
        "executed_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
)
