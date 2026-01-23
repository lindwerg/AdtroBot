"""Progress feedback for long-running AI operations.

Provides typing indicator + progress message for better UX during AI generation.
"""

from typing import Any, Coroutine

from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

# Progress message templates for different operation types
PROGRESS_MESSAGES: dict[str, str] = {
    "horoscope": "Генерирую гороскоп...",
    "tarot": "Создаю расклад таро...",
    "natal": "Анализирую натальную карту...",
    "default": "Обработка...",
}


async def generate_with_feedback(
    message: Message,
    operation_type: str,
    ai_coro: Coroutine[Any, Any, Any],
) -> Any:
    """Execute AI coroutine with typing indicator and progress message.

    Shows a progress message and typing indicator while the AI operation runs.
    The progress message is deleted after the operation completes (success or error).

    Args:
        message: Telegram message to send progress to (same chat)
        operation_type: Key from PROGRESS_MESSAGES (horoscope, tarot, natal)
        ai_coro: Coroutine to execute (e.g., ai_service.generate_premium_horoscope(...))

    Returns:
        Result of the ai_coro

    Example:
        result = await generate_with_feedback(
            message=callback.message,
            operation_type="horoscope",
            ai_coro=ai_service.generate_premium_horoscope(...)
        )
    """
    # Get progress message text
    progress_text = PROGRESS_MESSAGES.get(operation_type, PROGRESS_MESSAGES["default"])

    # Send progress message
    progress_msg = await message.answer(progress_text)

    try:
        # Run AI operation with typing indicator
        # interval=4.0 ensures typing is refreshed every 4 seconds
        async with ChatActionSender.typing(
            bot=message.bot,
            chat_id=message.chat.id,
            interval=4.0,
        ):
            result = await ai_coro

        return result
    finally:
        # Always delete progress message (ignore errors if already deleted)
        try:
            await progress_msg.delete()
        except Exception:
            pass
