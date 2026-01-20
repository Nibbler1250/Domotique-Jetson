"""Standard API response utilities."""

from datetime import datetime, timezone
from typing import Any


def api_response(data: Any, **meta: Any) -> dict[str, Any]:
    """Standard API response wrapper.

    Returns:
        { data: T, meta: { timestamp: ISO8601, ...meta } }
    """
    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **meta,
        },
    }
