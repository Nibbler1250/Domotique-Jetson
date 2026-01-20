"""Automations model using SQLAlchemy Core.

Automations represent scheduled or event-triggered actions.
This model tracks automation definitions and their execution history.
"""

from sqlalchemy import Boolean, DateTime, Integer, String, Table, Column, Text, text

from app.db.database import metadata


# Automations table - tracks automation definitions from Mistral Brain
automations = Table(
    "automations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("brain_name", String(100), unique=True, nullable=False, index=True),  # Name in Mistral Brain
    Column("label", String(100), nullable=False),
    Column("description", String(255), nullable=True),
    Column("trigger_type", String(50), nullable=True),  # time, event, device, manual
    Column("trigger_config", Text, nullable=True),  # JSON trigger configuration
    Column("actions_count", Integer, nullable=False, server_default=text("0")),
    Column("is_enabled", Boolean, nullable=False, server_default=text("1")),
    Column("last_triggered", DateTime(timezone=True), nullable=True),
    Column("last_success", Boolean, nullable=True),
    Column("trigger_count", Integer, nullable=False, server_default=text("0")),
    Column("success_count", Integer, nullable=False, server_default=text("0")),
    Column("failure_count", Integer, nullable=False, server_default=text("0")),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)


# Automation execution log - tracks each execution
automation_executions = Table(
    "automation_executions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("automation_id", Integer, nullable=True, index=True),  # Can be null for external triggers
    Column("brain_name", String(100), nullable=False, index=True),
    Column("triggered_by", String(50), nullable=True),  # schedule, event, user, brain
    Column("trigger_detail", String(255), nullable=True),  # Additional trigger info
    Column("success", Boolean, nullable=False),
    Column("actions_total", Integer, nullable=False),
    Column("actions_succeeded", Integer, nullable=False),
    Column("actions_failed", Integer, nullable=False),
    Column("duration_ms", Integer, nullable=True),  # Execution duration
    Column("error_message", Text, nullable=True),
    Column("error_details", Text, nullable=True),  # JSON array of action errors
    Column(
        "executed_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True,
    ),
)


# Alerts table - tracks system alerts and issues
alerts = Table(
    "alerts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("alert_type", String(50), nullable=False, index=True),  # automation_failure, device_offline, etc.
    Column("severity", String(20), nullable=False, server_default=text("'warning'")),  # info, warning, error, critical
    Column("source", String(100), nullable=True),  # automation name, device name, etc.
    Column("message", String(500), nullable=False),
    Column("details", Text, nullable=True),  # JSON additional details
    Column("is_acknowledged", Boolean, nullable=False, server_default=text("0")),
    Column("acknowledged_by", Integer, nullable=True),  # user_id
    Column("acknowledged_at", DateTime(timezone=True), nullable=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True,
    ),
)
