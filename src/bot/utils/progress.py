"""Progress feedback for long-running AI operations.

Provides typing indicator + animated progress bars for better UX during AI generation.
"""

import asyncio
from typing import Any, Coroutine

import structlog
from aiogram.types import Message

logger = structlog.get_logger()


# Operation configurations (базовое сообщение, время оценки, интервал обновления)
OPERATION_CONFIG = {
    "horoscope": {
        "base_message": "✨ Генерирую персональный прогноз",
        "estimated_seconds": 25,
        "update_interval": 2.0,
    },
    "natal_chart": {
        "base_message": "🌌 Генерирую натальную карту",
        "estimated_seconds": 40,
        "update_interval": 2.0,
    },
    "tarot": {
        "base_message": "🃏 Интерпретирую расклад",
        "estimated_seconds": 15,
        "update_interval": 2.0,
    },
    "card_of_day": {
        "base_message": "🔮 Генерирую карту дня",
        "estimated_seconds": 12,
        "update_interval": 2.0,
    },
    "natal": {
        "base_message": "🔮 Анализирую натальную карту",
        "estimated_seconds": 30,
        "update_interval": 2.0,
    },
    "default": {
        "base_message": "⏳ Обрабатываю запрос",
        "estimated_seconds": 20,
        "update_interval": 3.0,
    },
}


def get_progress_bar(percent: int, length: int = 10) -> str:
    """Generate visual progress bar.

    Args:
        percent: Progress percentage (0-100)
        length: Length of progress bar in characters

    Returns:
        Progress bar string like "▓▓▓▓░░░░░░"
    """
    filled = int(length * percent / 100)
    return "▓" * filled + "░" * (length - filled)


def estimate_progress(elapsed_seconds: float, estimated_total_seconds: float) -> int:
    """Estimate progress percentage based on elapsed time.

    Args:
        elapsed_seconds: Time elapsed since start
        estimated_total_seconds: Estimated total time for operation

    Returns:
        Progress percentage (0-95, never 100 to indicate still working)
    """
    if estimated_total_seconds <= 0:
        return 0
    percent = int((elapsed_seconds / estimated_total_seconds) * 100)
    return min(percent, 95)  # Cap at 95% to show it's still working


async def generate_with_feedback(
    message: Message,
    operation_type: str,
    ai_coro: Coroutine[Any, Any, Any],
) -> Any:
    """Execute AI coroutine with typing indicator and animated progress bar.

    Shows an animated progress bar that updates every 2-3 seconds based on
    estimated completion time for the operation type.

    Args:
        message: Telegram message to send progress to (same chat)
        operation_type: Operation key from OPERATION_CONFIG
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
    # Get operation config
    config = OPERATION_CONFIG.get(operation_type, OPERATION_CONFIG["default"])
    base_message = config["base_message"]
    estimated_seconds = config["estimated_seconds"]
    update_interval = config["update_interval"]

    # Initial message with estimated time
    initial_text = (
        f"{base_message}...\n"
        f"{get_progress_bar(0)}\n"
        f"0%\n\n"
        f"⏱ Примерное время: {estimated_seconds} сек"
    )
    progress_msg = await message.answer(initial_text)

    # Start AI generation task
    generation_task = asyncio.create_task(ai_coro)
    start_time = asyncio.get_event_loop().time()

    # Update progress bar while generating
    try:
        while not generation_task.done():
            await asyncio.sleep(update_interval)

            if not generation_task.done():
                # Calculate progress based on elapsed time
                elapsed = asyncio.get_event_loop().time() - start_time
                progress = estimate_progress(elapsed, estimated_seconds)

                # Update progress message
                try:
                    updated_text = (
                        f"{base_message}...\n" f"{get_progress_bar(progress)}\n" f"{progress}%"
                    )
                    await progress_msg.edit_text(updated_text)
                except Exception as e:
                    # Ignore edit errors (message might be deleted or unchanged)
                    logger.debug("progress_update_error", error=str(e))

        # Get result
        result = await generation_task
        return result

    except Exception as e:
        # Log error but re-raise
        logger.error(
            "ai_generation_error",
            operation_type=operation_type,
            error=str(e),
        )
        raise

    finally:
        # Always delete progress message
        try:
            await progress_msg.delete()
        except Exception:
            pass
