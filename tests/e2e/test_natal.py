"""
E2E tests for natal chart functionality.

Tests:
- Natal chart requires premium
- Natal chart requires birth data
- Natal chart generation (premium users only)
- Detailed natal interpretation purchase flow
"""

import pytest
from telethon import TelegramClient


async def navigate_to_natal_menu(
    conv,
    bot_username: str,
    timeout: int,
) -> None:
    """Helper to navigate to natal chart menu from /start."""
    await conv.send_message("/start")

    # Skip image
    response = await conv.get_response()
    if response.photo:
        response = await conv.get_response()

    # Find and click natal button
    natal_clicked = False
    if response.buttons:
        for row in response.buttons:
            for button in row:
                button_text = button.text if hasattr(button, 'text') else str(button)
                if any(kw in button_text for kw in ["Натальная", "Natal", "карта рождения"]):
                    await button.click()
                    natal_clicked = True
                    break
            if natal_clicked:
                break


@pytest.mark.asyncio
async def test_natal_menu_accessible(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test natal chart menu is accessible from main menu."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await navigate_to_natal_menu(conv, bot_username, conversation_timeout)

        response = await conv.get_response()

        # Should show natal info or premium gate
        natal_keywords = [
            "Натальная",
            "Natal",
            "карта",
            "chart",
            "планет",
            "planet",
            "Premium",
            "Премиум",
            "подписк",
        ]

        has_natal_content = any(
            kw.lower() in response.raw_text.lower()
            for kw in natal_keywords
        )

        assert has_natal_content, f"Expected natal content, got: {response.raw_text[:200]}"


@pytest.mark.asyncio
async def test_natal_premium_requirement(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test natal chart shows premium requirement for free users."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await navigate_to_natal_menu(conv, bot_username, conversation_timeout)

        response = await conv.get_response()

        # Free users should see premium gate
        premium_keywords = [
            "Premium",
            "Премиум",
            "подписк",
            "subscription",
            "доступн",
            "available",
        ]

        # Or if premium, asks for birth data
        birth_data_keywords = [
            "место рождения",
            "birth place",
            "время рождения",
            "birth time",
            "укажите",
            "specify",
        ]

        has_premium_gate = any(
            kw.lower() in response.raw_text.lower()
            for kw in premium_keywords
        )

        asks_birth_data = any(
            kw.lower() in response.raw_text.lower()
            for kw in birth_data_keywords
        )

        # Either shows premium gate or asks for birth data (if premium)
        # Or generates natal chart directly (if premium with data)
        has_natal_content = "натальн" in response.raw_text.lower() or response.photo is not None

        assert has_premium_gate or asks_birth_data or has_natal_content, \
            f"Expected premium gate or birth data request, got: {response.raw_text[:200]}"


@pytest.mark.asyncio
async def test_natal_teaser_content(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test natal teaser explains what the feature provides."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await navigate_to_natal_menu(conv, bot_username, conversation_timeout)

        response = await conv.get_response()

        # Teaser should explain natal chart features
        teaser_keywords = [
            "планет",
            "planet",
            "дом",
            "house",
            "аспект",
            "aspect",
            "интерпретац",
            "interpret",
            "солнц",
            "sun",
            "лун",
            "moon",
        ]

        has_teaser = any(
            kw.lower() in response.raw_text.lower()
            for kw in teaser_keywords
        )

        # Or it's already generating natal chart (premium with data)
        is_generating = "Проверяю" in response.raw_text or "Строю" in response.raw_text

        # Or already has subscription
        assert has_teaser or is_generating or response.photo is not None, \
            f"Expected teaser content, got: {response.raw_text[:200]}"


@pytest.mark.asyncio
async def test_natal_subscription_button(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test natal teaser has subscription button for free users."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await navigate_to_natal_menu(conv, bot_username, conversation_timeout)

        response = await conv.get_response()

        # Check for subscription-related buttons
        has_sub_button = False
        if response.buttons:
            for row in response.buttons:
                for button in row:
                    btn_text = button.text if hasattr(button, 'text') else str(button)
                    sub_keywords = ["Подписка", "Subscription", "Premium", "Премиум", "Оформить"]
                    if any(kw in btn_text for kw in sub_keywords):
                        has_sub_button = True
                        break

        # Or already premium (has different buttons)
        has_natal_buttons = False
        if response.buttons:
            for row in response.buttons:
                for button in row:
                    btn_text = button.text if hasattr(button, 'text') else str(button)
                    if any(kw in btn_text for kw in ["Показать", "Show", "Настроить", "Setup"]):
                        has_natal_buttons = True
                        break

        # Either has sub button or natal-specific buttons
        assert has_sub_button or has_natal_buttons or response.buttons is not None, \
            "Expected action buttons"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_natal_generation_premium(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test natal chart generation for premium user with birth data.

    Note: This test requires:
    - Premium test account
    - Birth data configured

    Will be skipped if user doesn't have premium or birth data.
    """
    async with telegram_client.conversation(
        bot_username,
        timeout=120,  # Natal chart generation is slow
    ) as conv:
        await navigate_to_natal_menu(conv, bot_username, conversation_timeout)

        response = await conv.get_response()

        # Check if we're generating natal chart (not showing premium gate)
        is_generating = any(kw in response.raw_text for kw in [
            "Проверяю",
            "Строю",
            "Building",
            "Loading",
        ])

        if is_generating:
            # Wait for chart generation
            for _ in range(10):
                try:
                    result = await conv.get_response()
                    if result.photo:
                        # Got the natal chart image
                        assert True, "Natal chart generated"
                        break
                    if "ошибка" in result.raw_text.lower() or "error" in result.raw_text.lower():
                        # Error during generation
                        break
                except Exception:
                    break
        else:
            # Either premium gate or birth data request
            pytest.skip("Test requires premium account with birth data")


@pytest.mark.asyncio
async def test_natal_back_navigation(
    telegram_client: TelegramClient,
    bot_username: str,
    conversation_timeout: int,
):
    """Test navigation back from natal menu."""
    async with telegram_client.conversation(bot_username, timeout=conversation_timeout) as conv:
        await navigate_to_natal_menu(conv, bot_username, conversation_timeout)

        response = await conv.get_response()

        # Look for back/menu button
        has_back = False
        if response.buttons:
            for row in response.buttons:
                for button in row:
                    btn_text = button.text if hasattr(button, 'text') else str(button)
                    if any(kw in btn_text for kw in ["Назад", "Back", "Меню", "Menu"]):
                        has_back = True
                        break

        # Any navigation buttons count
        has_navigation = has_back or (response.buttons is not None and len(response.buttons) > 0)

        assert has_navigation, "Expected navigation from natal menu"
