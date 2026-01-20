"""User profiles database model for themes and preferences."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.sql import func

from app.db.database import metadata

profiles = Table(
    "profiles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    ),
    # Theme settings
    Column("theme", String(50), nullable=False, server_default=text("'system'")),
    Column("color_scheme", String(50), nullable=True),  # Custom color overrides
    Column("font_size", String(20), nullable=False, server_default=text("'medium'")),
    Column("contrast", String(20), nullable=False, server_default=text("'normal'")),
    # Layout preferences
    Column("dashboard_layout", Text, nullable=True),  # JSON: widget positions
    Column("favorite_devices", Text, nullable=True),  # JSON: device IDs
    Column("default_room", String(100), nullable=True),
    Column("show_weather", Boolean, nullable=False, server_default=text("1")),
    Column("show_clock", Boolean, nullable=False, server_default=text("1")),
    # Accessibility
    Column("reduce_motion", Boolean, nullable=False, server_default=text("0")),
    Column("high_contrast", Boolean, nullable=False, server_default=text("0")),
    Column("large_touch_targets", Boolean, nullable=False, server_default=text("0")),
    # Kiosk mode specific
    Column("kiosk_auto_dim", Boolean, nullable=False, server_default=text("1")),
    Column("kiosk_dim_start", String(5), nullable=True),  # HH:MM format
    Column("kiosk_dim_end", String(5), nullable=True),  # HH:MM format
    Column("kiosk_dim_brightness", Integer, nullable=False, server_default=text("30")),
    # Timestamps
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    ),
)

# Available themes
THEMES = ["system", "light", "dark", "simon", "caroline", "kids", "kiosk"]

# Font sizes
FONT_SIZES = ["small", "medium", "large", "xlarge"]

# Contrast levels
CONTRAST_LEVELS = ["normal", "high", "highest"]
