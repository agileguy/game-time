"""Structured logging configuration using loguru."""

import json
import sys
from typing import Any

from loguru import logger

from app.config import settings


def serialize_log_record(record: dict[str, Any]) -> str:
    """
    Serialize log record to JSON format.

    Args:
        record: Log record dictionary

    Returns:
        str: JSON-formatted log string
    """
    log_data = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add exception info if present
    if record["exception"]:
        log_data["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }

    # Add extra fields
    if "extra" in record and record["extra"]:
        log_data["extra"] = record["extra"]

    return json.dumps(log_data)


def configure_logging() -> None:
    """Configure application logging."""
    # Remove default handler
    logger.remove()

    # Determine log format
    if settings.log_format == "json":
        # JSON format for production
        logger.add(
            sys.stdout,
            format=serialize_log_record,
            level=settings.log_level,
            serialize=False,
        )
    else:
        # Human-readable format for development
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
            level=settings.log_level,
            colorize=True,
        )

    # Add file logging for production
    if not settings.debug:
        logger.add(
            "logs/app.log",
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            format=serialize_log_record,
            level=settings.log_level,
        )


def get_logger() -> logger:
    """
    Get configured logger instance.

    Returns:
        logger: Configured loguru logger
    """
    return logger


# Configure logging on module import
configure_logging()
