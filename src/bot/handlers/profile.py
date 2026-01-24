"""Profile settings handlers."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.menu import MenuAction, MenuCallback
from src.bot.callbacks.profile import (
    NotificationTimeCallback,
    NotificationToggleCallback,
    TimezoneCallback,
)
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.keyboards.profile import (
    TIMEZONES,
    build_notification_time_keyboard,
    build_notifications_toggle_keyboard,
    build_timezone_keyboard,
)
from src.db.models.user import User
from src.services.scheduler import remove_user_notification, schedule_user_notification

router = Router(name="profile_settings")


@router.callback_query(MenuCallback.filter(F.action == MenuAction.PROFILE_NOTIFICATIONS))
async def settings_notifications_callback(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Show notification settings from inline button."""
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Профиль не найден. Нажмите /start", show_alert=True)
        return

    # Get timezone label
    tz_label = user.timezone or "Europe/Moscow"
    for zone, label in TIMEZONES:
        if zone == user.timezone:
            tz_label = label
            break

    status = "включены" if user.notifications_enabled else "выключены"
    hour = user.notification_hour or 9

    text = (
        f"Настройки уведомлений\n\n"
        f"Статус: {status}\n"
        f"Время: {hour:02d}:00\n"
        f"Часовой пояс: {tz_label}\n\n"
        "Выберите действие:"
    )

    await callback.message.edit_text(
        text, reply_markup=build_notifications_toggle_keyboard(user.notifications_enabled)
    )
    await callback.answer()


@router.callback_query(NotificationToggleCallback.filter())
async def toggle_notifications(
    callback: CallbackQuery,
    callback_data: NotificationToggleCallback,
    session: AsyncSession,
) -> None:
    """Toggle notifications on/off."""
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    user.notifications_enabled = callback_data.enable
    await session.commit()

    if callback_data.enable:
        # Schedule notification
        if user.zodiac_sign:
            schedule_user_notification(
                user_id=user.telegram_id,
                hour=user.notification_hour or 9,
                timezone=user.timezone or "Europe/Moscow",
                zodiac_sign=user.zodiac_sign,
            )
        await callback.message.edit_text(
            "Уведомления включены! Выберите время:",
            reply_markup=build_notification_time_keyboard(),
        )
    else:
        # Remove notification
        remove_user_notification(user.telegram_id)
        await callback.message.edit_text("Уведомления выключены.")

    await callback.answer()


@router.callback_query(NotificationTimeCallback.filter())
async def set_notification_time(
    callback: CallbackQuery,
    callback_data: NotificationTimeCallback,
    session: AsyncSession,
) -> None:
    """Set notification time."""
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    user.notification_hour = callback_data.hour
    await session.commit()

    # Reschedule notification with new time
    if user.notifications_enabled and user.zodiac_sign:
        schedule_user_notification(
            user_id=user.telegram_id,
            hour=callback_data.hour,
            timezone=user.timezone or "Europe/Moscow",
            zodiac_sign=user.zodiac_sign,
        )

    await callback.message.edit_text(
        f"Время установлено: {callback_data.hour:02d}:00\n\nВыберите часовой пояс:",
        reply_markup=build_timezone_keyboard(),
    )
    await callback.answer()


@router.callback_query(TimezoneCallback.filter())
async def set_timezone(
    callback: CallbackQuery,
    callback_data: TimezoneCallback,
    session: AsyncSession,
) -> None:
    """Set user timezone."""
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    user.timezone = callback_data.zone
    await session.commit()

    # Reschedule notification with new timezone
    if user.notifications_enabled and user.zodiac_sign:
        schedule_user_notification(
            user_id=user.telegram_id,
            hour=user.notification_hour or 9,
            timezone=callback_data.zone,
            zodiac_sign=user.zodiac_sign,
        )

    # Get timezone label
    tz_label = callback_data.zone
    for zone, label in TIMEZONES:
        if zone == callback_data.zone:
            tz_label = label
            break

    await callback.message.edit_text(
        f"Настройки сохранены!\n\n"
        f"Уведомления: включены\n"
        f"Время: {user.notification_hour or 9:02d}:00\n"
        f"Часовой пояс: {tz_label}"
    )
    # Show main menu after timezone selection
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
