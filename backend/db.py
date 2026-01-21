"""
Database setup for Roboto SAI backend (SQLite + SQLAlchemy async).
"""

import os
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/roboto.db")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()
logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        try:
            result = await conn.exec_driver_sql("PRAGMA table_info(messages)")
            columns = {row[1] for row in result}
            alter_statements = []
            if "user_id" not in columns:
                alter_statements.append("ALTER TABLE messages ADD COLUMN user_id TEXT")
            if "emotion" not in columns:
                alter_statements.append("ALTER TABLE messages ADD COLUMN emotion TEXT")
            if "emotion_text" not in columns:
                alter_statements.append("ALTER TABLE messages ADD COLUMN emotion_text TEXT")
            if "emotion_probabilities" not in columns:
                alter_statements.append("ALTER TABLE messages ADD COLUMN emotion_probabilities TEXT")

            for statement in alter_statements:
                await conn.exec_driver_sql(statement)
        except Exception as exc:
            logger.warning(f"Failed to ensure emotion columns: {exc}")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations."""
    async with AsyncSessionLocal() as session:
        yield session
