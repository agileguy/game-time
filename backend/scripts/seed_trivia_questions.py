"""Seed trivia questions from JSON file into database."""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.logging import logger  # noqa: E402
from app.database import AsyncSessionLocal, init_db  # noqa: E402
from app.models.trivia_question import TriviaQuestion  # noqa: E402


async def seed_questions() -> None:
    """Load trivia questions from JSON file into database."""
    # Path to the JSON file
    json_path = Path(__file__).parent.parent / "app" / "games" / "trivia_questions.json"

    if not json_path.exists():
        logger.error(f"Questions file not found: {json_path}")
        sys.exit(1)

    # Load questions from JSON
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            questions_data = data.get("questions", [])
    except Exception as e:
        logger.error(f"Failed to load questions from JSON: {e}")
        sys.exit(1)

    if not questions_data:
        logger.error("No questions found in JSON file")
        sys.exit(1)

    logger.info(f"Loaded {len(questions_data)} questions from JSON")

    # Insert questions into database
    async with AsyncSessionLocal() as db:
        try:
            # Check if questions already exist
            result = await db.execute(select(TriviaQuestion))
            existing_questions = result.scalars().all()

            if existing_questions:
                logger.info(
                    f"Database already contains {len(existing_questions)} questions"
                )
                response = input("Delete existing questions and reseed? (y/N): ")
                if response.lower() != "y":
                    logger.info("Skipping seed operation")
                    return

                # Delete existing questions
                for question in existing_questions:
                    await db.delete(question)
                await db.commit()
                logger.info("Deleted existing questions")

            # Insert new questions
            added_count = 0
            for q_data in questions_data:
                question = TriviaQuestion(
                    question=q_data["question"],
                    options=q_data["options"],
                    correct_answer=q_data["correct_answer"],
                    category=q_data["category"],
                    difficulty=q_data["difficulty"],
                )
                db.add(question)
                added_count += 1

            await db.commit()
            logger.info(f"Successfully seeded {added_count} trivia questions!")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to seed questions: {e}")
            sys.exit(1)


async def main() -> None:
    """Initialize database and seed questions."""
    try:
        # Initialize database tables
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully!")

        # Seed questions
        await seed_questions()

    except Exception as e:
        logger.error(f"Failed to seed trivia questions: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
