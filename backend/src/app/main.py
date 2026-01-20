"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.response import api_response
from app.db.database import dispose_engine, get_connection, init_db
from app.api.v1 import activity as activity_router
from app.api.v1 import auth as auth_router
from app.api.v1 import automations as automations_router
from app.api.v1 import config as config_router
from app.api.v1 import devices as devices_router
from app.api.v1 import health as health_router
from app.api.v1 import integrations as integrations_router
from app.api.v1 import kiosk as kiosk_router
from app.api.v1 import modes as modes_router
from app.api.v1 import permissions as permissions_router
from app.api.v1 import profiles as profiles_router
from app.api.v1 import temperature as temperature_router
from app.api.v1 import users as users_router
from app.api.v1 import websocket as ws_router
from app.api.v1 import trading as trading_router
from app.services.mqtt import get_mqtt_service
from app.services.modes import create_default_modes
from app.services.users import create_default_users

settings = get_settings()

# Background task for MQTT
_mqtt_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    global _mqtt_task

    # Startup
    await init_db()
    # Create default users and modes
    async with get_connection() as conn:
        await create_default_users(conn)
        await create_default_modes(conn)

    # Start MQTT service in background
    mqtt_service = get_mqtt_service()
    _mqtt_task = asyncio.create_task(mqtt_service.start())

    yield

    # Shutdown
    if _mqtt_task:
        await mqtt_service.stop()
        _mqtt_task.cancel()
        try:
            await _mqtt_task
        except asyncio.CancelledError:
            pass

    await dispose_engine()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(activity_router.router, prefix=settings.api_v1_prefix)
app.include_router(auth_router.router, prefix=settings.api_v1_prefix)
app.include_router(automations_router.router, prefix=settings.api_v1_prefix)
app.include_router(config_router.router, prefix=settings.api_v1_prefix)
app.include_router(devices_router.router, prefix=settings.api_v1_prefix)
app.include_router(health_router.router, prefix=settings.api_v1_prefix)
app.include_router(integrations_router.router, prefix=settings.api_v1_prefix)
app.include_router(kiosk_router.router, prefix=settings.api_v1_prefix)
app.include_router(modes_router.router, prefix=settings.api_v1_prefix)
app.include_router(permissions_router.router, prefix=settings.api_v1_prefix)
app.include_router(profiles_router.router, prefix=settings.api_v1_prefix)
app.include_router(temperature_router.router, prefix=settings.api_v1_prefix)
app.include_router(users_router.router, prefix=settings.api_v1_prefix)
app.include_router(ws_router.router, prefix=settings.api_v1_prefix)
app.include_router(trading_router.router, prefix=settings.api_v1_prefix)


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return api_response(
        {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }
    )


@app.get("/api/v1/ping")
async def ping() -> dict[str, Any]:
    """Simple ping endpoint for connectivity testing."""
    return api_response({"pong": True})
