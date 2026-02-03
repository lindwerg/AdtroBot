"""Safe message editing utilities for text/photo messages."""
import structlog
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

logger = structlog.get_logger()


async def safe_edit_message(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    """Safely edit message - handles both text and photo messages.

    For photo messages: deletes old message and sends new text message.
    For text messages: edits text in place.

    Args:
        callback: CallbackQuery to edit
        text: New text content
        reply_markup: Optional keyboard
        parse_mode: Optional parse mode (Markdown, HTML)
    """
    try:
        if callback.message.photo:
            # Photo message - delete and resend as text
            await callback.message.delete()
            await callback.message.answer(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            logger.debug(
                "safe_edit_photo_to_text",
                user_id=callback.from_user.id,
            )
        else:
            # Text message - edit in place
            await callback.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            logger.debug(
                "safe_edit_text",
                user_id=callback.from_user.id,
            )
    except Exception as e:
        # Fallback: delete and resend
        logger.warning(
            "safe_edit_fallback",
            error=str(e),
            user_id=callback.from_user.id,
        )
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
