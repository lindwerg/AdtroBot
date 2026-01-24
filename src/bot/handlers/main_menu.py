"""Обработчик главного меню с информативным блоком."""

from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.utils.natal_info_formatter import format_natal_info_for_menu
from src.db.models.user import User
from src.services.astrology.natal_chart import calculate_full_natal_chart


async def show_main_menu(message: Message, session: AsyncSession) -> None:
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
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Пользователь не найден — показать базовое меню
        await message.answer(
            "Главное меню 🏠",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Определить какую информацию показывать
    natal_data = None

    # Если premium И есть натальные данные — вычислить натальную карту
    if user.is_premium and _has_natal_data(user):
        try:
            # Расчёт натальной карты (~100-150ms)
            natal_data = calculate_full_natal_chart(
                birth_date=user.birth_date,
                birth_time=user.birth_time,
                latitude=user.birth_lat,
                longitude=user.birth_lon,
                timezone_str=user.timezone or "Europe/Moscow",
            )
        except Exception:
            # Если расчёт failed — показать без натальных данных
            natal_data = None

    # Сформировать информативный блок
    info_block = format_natal_info_for_menu(user, natal_data)

    # Отправить сообщение с информацией + клавиатура
    await message.answer(
        f"Главное меню 🏠\n\n{info_block}",
        reply_markup=get_main_menu_keyboard(),
    )


def _has_natal_data(user: User) -> bool:
    """Проверить, заполнил ли пользователь натальные данные.

    Args:
        user: Пользователь

    Returns:
        True если все обязательные поля заполнены
    """
    return (
        user.birth_date is not None
        and user.birth_lat is not None
        and user.birth_lon is not None
    )
