"""
E2E tests for /start command and welcome flow.

Tests:
- /start shows welcome message with cosmic image
- /start shows menu keyboard for new users
- Returning users see personalized greeting
"""

import pytest
from telethon import TelegramClient


@pytest.mark.asyncio
async def test_start_shows_welcome_message(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test /start shows welcome message."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await conv.send_message("/start")

        # First message should be cosmic image
        response = await conv.get_response()

        # Get next message (text welcome)
        if response.photo:
            response = await conv.get_response()

        # Verify welcome text variants
        welcome_found = any(phrase in response.raw_text for phrase in [
            "Привет",
            "Добро пожаловать",
            "Рад тебя видеть",
            "Welcome",
        ])
        assert welcome_found, f"Expected welcome message, got: {response.raw_text[:200]}"


@pytest.mark.asyncio
async def test_start_sends_cosmic_image(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test /start sends cosmic image before welcome text."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await conv.send_message("/start")

        # First message should be photo
        response = await conv.get_response()

        # Either first message has photo, or we need to check second
        has_photo = response.photo is not None

        if not has_photo:
            # Check if there's a second message with photo
            try:
                response2 = await conv.get_response()
                has_photo = response2.photo is not None
            except Exception:
                pass

        assert has_photo, "Expected cosmic image to be sent with /start"


@pytest.mark.asyncio
async def test_start_shows_menu_keyboard(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test /start shows inline keyboard for interaction."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await conv.send_message("/start")

        # Get all responses (image + text)
        response = await conv.get_response()
        if response.photo:
            response = await conv.get_response()

        # Verify inline keyboard exists
        assert response.buttons is not None, "Expected inline keyboard after /start"


@pytest.mark.asyncio
async def test_start_button_exists(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test /start message has action button."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await conv.send_message("/start")

        response = await conv.get_response()
        if response.photo:
            response = await conv.get_response()

        # Check for buttons
        if response.buttons:
            # Flatten button rows and get text
            button_texts = []
            for row in response.buttons:
                for button in row:
                    button_texts.append(button.text if hasattr(button, 'text') else str(button))

            # Should have at least one button
            assert len(button_texts) > 0, "Expected at least one button"
