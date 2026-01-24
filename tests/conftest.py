"""
Pytest configuration and fixtures for E2E and integration tests.

Provides:
- TelegramClient fixture for Telethon bot testing
- Database session fixtures with cleanup
- Test data factories
"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from telethon import TelegramClient
from telethon.sessions import StringSession


# Telethon credentials from environment
API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
TELETHON_SESSION = os.environ.get("TELETHON_SESSION", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@AdtroBot")


@pytest.fixture(scope="session")
def bot_username() -> str:
    """Get bot username from environment."""
    return BOT_USERNAME


@pytest_asyncio.fixture(scope="session")
async def telegram_client() -> AsyncGenerator[TelegramClient, None]:
    """
    Create a Telethon TelegramClient for E2E testing.

    Requires environment variables:
    - TELEGRAM_API_ID: Telegram API ID
    - TELEGRAM_API_HASH: Telegram API hash
    - TELETHON_SESSION: StringSession string (for CI/headless)

    Usage:
        async def test_start_command(telegram_client, bot_username):
            async with telegram_client:
                await telegram_client.send_message(bot_username, "/start")
                response = await telegram_client.get_messages(bot_username, limit=1)
                assert "Добро пожаловать" in response[0].text
    """
    if not API_ID or not API_HASH:
        pytest.skip(
            "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set for Telegram E2E tests"
        )

    # Use StringSession for stateless authentication (CI-friendly)
    session = StringSession(TELETHON_SESSION)
    client = TelegramClient(
        session,
        int(API_ID),
        API_HASH,
        sequential_updates=True,  # Ensures ordered message delivery
    )

    await client.start()
    yield client
    await client.disconnect()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for tests with automatic cleanup.

    Uses TEST_DATABASE_URL if set, otherwise falls back to DATABASE_URL.
    """
    database_url = os.environ.get(
        "TEST_DATABASE_URL",
        os.environ.get("DATABASE_URL", "")
    )

    if not database_url:
        pytest.skip("DATABASE_URL or TEST_DATABASE_URL must be set for database tests")

    # Replace postgres:// with postgresql+asyncpg:// for async support
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()

    await engine.dispose()


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
