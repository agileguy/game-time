"""Main FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_db, init_db
from app.redis_client import redis_client
from app.routes import health, rooms, websocket


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    await init_db()
    await redis_client.connect()
    yield
    # Shutdown
    await close_db()
    await redis_client.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Multiplayer party game platform with dual-screen experience",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(rooms.router)
app.include_router(websocket.router)


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Root endpoint.

    Returns:
        JSONResponse: API information
    """
    return JSONResponse(
        content={
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }
    )
