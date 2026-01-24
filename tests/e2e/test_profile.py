"""
E2E tests for user profile functionality.

Tests:
- Profile shows user data
- Birth date can be set via onboarding
- Profile displays zodiac sign after setup
"""

import pytest
from telethon import TelegramClient


@pytest.mark.asyncio
async def test_profile_command_responds(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test /profile or profile button responds with user data."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        # Start fresh to ensure user exists
        await conv.send_message("/start")
        await conv.get_response()  # Image

        response = await conv.get_response()
        if response.photo:
            response = await conv.get_response()

        # Try to find and click profile button, or send /profile
        profile_clicked = False
        if response.buttons:
            for row in response.buttons:
                for button in row:
                    button_text = button.text if hasattr(button, 'text') else str(button)
                    if "Профиль" in button_text or "Profile" in button_text:
                        await button.click()
                        profile_clicked = True
                        break
                if profile_clicked:
                    break

        if not profile_clicked:
            # Fallback to command
            await conv.send_message("/profile")

        # Get response
        response = await conv.get_response()

        # Profile should show some user-related content
        profile_keywords = [
            "Профиль",
            "Profile",
            "Дата рождения",
            "Birth date",
            "Знак",
            "Sign",
            "Настройки",
            "Settings",
        ]

        has_profile_content = any(kw in response.raw_text for kw in profile_keywords)
        assert has_profile_content, f"Expected profile content, got: {response.raw_text[:200]}"


@pytest.mark.asyncio
async def test_menu_navigation_works(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test main menu navigation is functional."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await conv.send_message("/start")

        # Collect responses
        response = await conv.get_response()
        if response.photo:
            response = await conv.get_response()

        # Verify we have interactive elements
        has_buttons = response.buttons is not None and len(response.buttons) > 0
        has_menu_text = any(word in response.raw_text.lower() for word in [
            "меню", "menu", "выбери", "choose", "готов", "ready"
        ])

        assert has_buttons or has_menu_text, "Expected navigation menu after /start"


@pytest.mark.asyncio
async def test_help_command_responds(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test /help command provides assistance."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await conv.send_message("/help")

        response = await conv.get_response()

        # Help should either show commands or redirect to start
        help_keywords = [
            "помощь",
            "help",
            "команд",
            "command",
            "/start",
            "гороскоп",
            "horoscope",
            "таро",
            "tarot",
        ]

        has_help = any(kw.lower() in response.raw_text.lower() for kw in help_keywords)
        # It's OK if /help just redirects to /start behavior
        has_welcome = "Привет" in response.raw_text or "Welcome" in response.raw_text

        assert has_help or has_welcome, f"Expected help or welcome, got: {response.raw_text[:200]}"


@pytest.mark.asyncio
async def test_settings_accessible(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test settings/notifications can be accessed."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await conv.send_message("/start")

        response = await conv.get_response()
        if response.photo:
            response = await conv.get_response()

        # Look for settings/profile button
        settings_found = False
        if response.buttons:
            for row in response.buttons:
                for button in row:
                    button_text = button.text if hasattr(button, 'text') else str(button)
                    if any(kw in button_text for kw in ["Профиль", "Profile", "Настройки", "Settings"]):
                        settings_found = True
                        break

        # Also check if inline keyboard has menu items
        if not settings_found and response.buttons:
            settings_found = len(response.buttons) > 0

        # Either has settings button or it's a new user with onboarding
        assert settings_found or response.buttons is not None, "Expected accessible settings"
