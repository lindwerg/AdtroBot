"""
E2E test fixtures for Telegram bot testing.

Extends base conftest.py with e2e-specific fixtures:
- cleanup_test_user: Removes test user after test
- conversation_timeout: 30s for AI responses
- bot_username: From env BOT_USERNAME
"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import telegram_client, db_session, bot_username  # noqa: F401

# Re-export fixtures from base conftest for convenience
__all__ = [
    "telegram_client",
    "db_session",
    "bot_username",
    "conversation_timeout",
    "cleanup_test_user",
]


# Default conversation timeout (AI responses are slow)
DEFAULT_CONVERSATION_TIMEOUT = 30


@pytest.fixture(scope="session")
def conversation_timeout() -> int:
    """Timeout for Telegram conversations with AI bot.

    Returns:
        Timeout in seconds (default 30s for AI responses)
    """
    return int(os.environ.get("E2E_CONVERSATION_TIMEOUT", DEFAULT_CONVERSATION_TIMEOUT))


@pytest_asyncio.fixture(scope="function")
async def cleanup_test_user(
    db_session: AsyncSession,
) -> AsyncGenerator[None, None]:
    """Cleanup fixture that removes test user data after test.

    Usage:
        async def test_something(cleanup_test_user, telegram_client):
            # Test code here
            # User data will be cleaned up automatically

    Note:
        This fixture yields before the test runs, allowing the test
        to create data, then cleans up after the test completes.
    """
    yield

    # Import here to avoid circular imports
    from src.db.models.user import User
    from src.db.models.tarot_spread import TarotSpread

    # Get test user telegram_id from environment
    test_telegram_id = os.environ.get("TEST_TELEGRAM_ID")

    if test_telegram_id:
        try:
            telegram_id = int(test_telegram_id)

            # Delete related tarot spreads first (foreign key constraint)
            await db_session.execute(
                delete(TarotSpread).where(
                    TarotSpread.user_id.in_(
                        db_session.query(User.id).filter(
                            User.telegram_id == telegram_id
                        )
                    )
                )
            )

            # Delete test user
            await db_session.execute(
                delete(User).where(User.telegram_id == telegram_id)
            )

            await db_session.commit()
        except (ValueError, Exception):
            # Ignore cleanup errors - best effort
            await db_session.rollback()
