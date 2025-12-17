"""Database initialization script."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db
from app.core.logging import logger


async def main() -> None:
    """Initialize database tables."""
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
