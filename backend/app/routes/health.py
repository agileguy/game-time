"""Health check endpoints."""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
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
        dict: Health status
    """
    return {"status": "healthy", "service": "game-time"}


@router.get("/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    """
    Database health check.

    Args:
        db: Database session

    Returns:
        dict: Database health status
    """
    try:
        # Execute a simple query
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "error": str(e)}


@router.get("/redis")
async def redis_health(redis: aioredis.Redis = Depends(get_redis)):
    """
    Redis health check.

    Args:
        redis: Redis client

    Returns:
        dict: Redis health status
    """
    try:
        # Ping Redis
        await redis.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "error", "error": str(e)}


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
        dict: Full health status
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
        await redis.ping()
    except Exception as e:
        redis_healthy = False
        errors.append(f"Redis: {str(e)}")

    overall_healthy = db_healthy and redis_healthy

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "database": "connected" if db_healthy else "error",
        "redis": "connected" if redis_healthy else "error",
        "errors": errors if errors else None,
    }
