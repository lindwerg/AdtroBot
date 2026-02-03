"""Error handling middleware."""
import structlog
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery

logger = structlog.get_logger()


class ErrorHandlerMiddleware(BaseMiddleware):
    """Catch all unhandled exceptions in handlers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(
                "handler_exception",
                error=str(e),
                error_type=type(e).__name__,
                event_type=type(event).__name__,
                user_id=getattr(event.from_user, "id", None) if hasattr(event, "from_user") else None,
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
