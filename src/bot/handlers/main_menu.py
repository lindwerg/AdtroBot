"""Обработчик главного меню с информативным блоком."""

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.utils.images import BotImages, get_image
from src.bot.utils.natal_info_formatter import format_natal_info_for_menu
from src.db.models.user import User
from src.services.astrology.natal_chart import calculate_full_natal_chart


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
    text = f"Главное меню 🏠\n\n{info_block}"
    keyboard = get_main_menu_keyboard()
    
    # Получаем изображение
    image = get_image(BotImages.WELCOME)
    send_chat_id = chat_id if chat_id is not None else message.chat.id

    if bot:
        # Используем bot когда message удалено (callback)
        if image:
            await bot.send_photo(chat_id=send_chat_id, photo=image, caption=text, reply_markup=keyboard)
        else:
            await bot.send_message(chat_id=send_chat_id, text=text, reply_markup=keyboard)
    else:
        # Используем message.answer для обычных команд
        if image:
            await message.answer_photo(photo=image, caption=text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)


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
