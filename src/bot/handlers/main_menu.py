"""Обработчик главного меню с информативным блоком."""

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.utils.natal_info_formatter import format_natal_info_for_menu
from src.db.models.user import User


async def show_main_menu(
    message: Message,
    session: AsyncSession,
    bot: Bot | None = None,
    user_id: int | None = None,
    chat_id: int | None = None,
) -> None:
    """Показать главное меню с информативным блоком.

    Логика:
    - Free пользователи: тизер премиум-функций
    - Premium без натальных данных: предложение заполнить
    - Premium с натальными данными: персональная натальная информация

    Args:
        message: Сообщение от пользователя
        session: Database session
    """
    # Загрузить пользователя из БД
    telegram_id = user_id if user_id is not None else message.from_user.id
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Пользователь не найден — показать базовое меню
        text = "Главное меню 🏠"
        keyboard = get_main_menu_keyboard()

        if bot:
            send_chat_id = chat_id if chat_id is not None else message.chat.id
            await bot.send_message(chat_id=send_chat_id, text=text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)
        return

    # Определить какую информацию показывать
    # PERFORMANCE FIX: Don't recalculate natal chart on every menu display
    # Just check if user has natal data - the formatter will handle display
    natal_data = None

    # Note: We intentionally skip calculate_full_natal_chart() here to avoid
    # blocking the menu display for 5-15 seconds. The natal chart is calculated
    # on-demand when user requests horoscope/natal readings.
    #
    # If needed in the future, pre-calculation can be done in background task
    # after user completes natal data setup.

    # Сформировать информативный блок
    info_block = format_natal_info_for_menu(user, natal_data)

    # Отправить сообщение с информацией + клавиатура
    text = f"Главное меню 🏠\n\n{info_block}"
    keyboard = get_main_menu_keyboard()

    if bot:
        # Используем bot.send_message когда message удалено (callback)
        await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard)
    else:
        # Используем message.answer для обычных команд
        await message.answer(text, reply_markup=keyboard)


def _has_natal_data(user: User) -> bool:
    """Проверить, заполнил ли пользователь натальные данные.

    Args:
        user: Пользователь

    Returns:
        True если все обязательные поля заполнены
    """
    return user.birth_date is not None and user.birth_lat is not None and user.birth_lon is not None
