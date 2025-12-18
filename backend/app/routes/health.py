"""Health check endpoints."""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis_client import get_redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Basic health check.

    Returns:
        dict: Health status with version
    """
    return {"status": "healthy", "service": "game-time", "version": "0.1.0"}


@router.get("/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    """
    Database health check.

    Args:
        db: Database session

    Returns:
        JSONResponse: Database health status with appropriate status code
    """
    try:
        # Execute a simple query
        await db.execute(text("SELECT 1"))
        return JSONResponse(
            content={"status": "healthy", "database": "connected"},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "unhealthy", "database": "error", "error": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.get("/redis")
async def redis_health(redis: aioredis.Redis = Depends(get_redis)):
    """
    Redis health check.

    Args:
        redis: Redis client

    Returns:
        JSONResponse: Redis health status with appropriate status code
    """
    try:
        # Ping Redis
        await redis.ping()  # type: ignore[misc]
        return JSONResponse(
            content={"status": "healthy", "redis": "connected"},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "unhealthy", "redis": "error", "error": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Readiness check endpoint.

    Verifies database and Redis connections.

    Args:
        db: Database session
        redis: Redis client

    Returns:
        JSONResponse: Readiness status with appropriate status code
    """
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))

        # Check Redis connection
        await redis.ping()  # type: ignore[misc]

        return JSONResponse(
            content={
                "status": "ready",
                "database": "connected",
                "redis": "connected",
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not ready",
                "error": str(e),
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.get("/full")
async def full_health_check(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Full health check (database + redis).

    Args:
        db: Database session
        redis: Redis client

    Returns:
        JSONResponse: Full health status with appropriate status code
    """
    db_healthy = True
    redis_healthy = True
    errors = []

    # Check database
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_healthy = False
        errors.append(f"Database: {str(e)}")

    # Check Redis
    try:
        await redis.ping()  # type: ignore[misc]
    except Exception as e:
        redis_healthy = False
        errors.append(f"Redis: {str(e)}")

    overall_healthy = db_healthy and redis_healthy

    return JSONResponse(
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "database": "connected" if db_healthy else "error",
            "redis": "connected" if redis_healthy else "error",
            "errors": errors if errors else None,
        },
        status_code=status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
