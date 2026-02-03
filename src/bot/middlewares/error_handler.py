"""Error handling middleware."""
import time
from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

logger = structlog.get_logger()


class ErrorHandlerMiddleware(BaseMiddleware):
    """Catch all unhandled exceptions in handlers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start_time = time.time()

        try:
            result = await handler(event, data)

            # Log slow handlers (>1 second)
            duration = time.time() - start_time
            if duration > 1.0:
                logger.warning(
                    "slow_handler",
                    event_type=type(event).__name__,
                    duration=round(duration, 2),
                    user_id=getattr(event.from_user, "id", None)
                    if hasattr(event, "from_user")
                    else None,
                    callback_data=event.data if isinstance(event, CallbackQuery) else None,
                )

            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "handler_exception",
                error=str(e),
                error_type=type(e).__name__,
                event_type=type(event).__name__,
                duration=round(duration, 2),
                user_id=getattr(event.from_user, "id", None)
                if hasattr(event, "from_user")
                else None,
            )

            # Answer callback to remove loading state
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
                except Exception:
                    pass

            # DON'T re-raise - let webhook return 200
            # Telegram retries if we raise, causing duplicates
            return None
