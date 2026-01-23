"""Birth data collection handlers for premium users."""

import re
from datetime import time

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.birth_data import CitySelectCallback, SkipTimeCallback
from src.bot.keyboards.birth_data import (
    build_birth_data_complete_keyboard,
    build_city_selection_keyboard,
    build_skip_time_keyboard,
)
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.states.birth_data import BirthDataStates
from src.db.models.user import User
from src.services.astrology.geocoding import CityResult, search_city

logger = structlog.get_logger()

router = Router(name="birth_data")

# Regex for time validation (HH:MM format)
TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})$")


@router.callback_query(F.data == "setup_birth_data")
async def start_birth_data_setup(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Start birth data collection flow (button in profile)."""
    await callback.answer()

    # Check if user is premium
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.message.edit_text(
            "Профиль не найден. Нажмите /start для регистрации."
        )
        return

    if not user.is_premium:
        await callback.message.edit_text(
            "Настройка натальной карты доступна только премиум-пользователям.\n\n"
            "Оформите подписку, чтобы получить персонализированные гороскопы!"
        )
        return

    # Start FSM
    await state.set_state(BirthDataStates.waiting_birth_time)

    await callback.message.edit_text(
        "Для построения натальной карты укажите время рождения.\n\n"
        "Введите время в формате ЧЧ:ММ (например, 14:30).\n\n"
        "Если не знаете точное время — нажмите кнопку ниже.",
        reply_markup=build_skip_time_keyboard(),
    )


@router.callback_query(SkipTimeCallback.filter(), BirthDataStates.waiting_birth_time)
async def skip_birth_time(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Skip birth time - will use noon for calculations."""
    await callback.answer()

    await state.update_data(birth_time=None)
    await state.set_state(BirthDataStates.waiting_birth_city)

    await callback.message.edit_text(
        "Хорошо, время не указано. Будет использовано полуденное время (12:00).\n\n"
        "Теперь введите город рождения (на русском или английском):"
    )


@router.message(BirthDataStates.waiting_birth_time)
async def process_birth_time(
    message: Message,
    state: FSMContext,
) -> None:
    """Parse and validate birth time input."""
    text = message.text.strip()
    match = TIME_PATTERN.match(text)

    if not match:
        await message.answer(
            "Неверный формат времени. Введите в формате ЧЧ:ММ (например, 14:30).",
            reply_markup=build_skip_time_keyboard(),
        )
        return

    hour, minute = int(match.group(1)), int(match.group(2))

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer(
            "Некорректное время. Часы: 0-23, минуты: 0-59.",
            reply_markup=build_skip_time_keyboard(),
        )
        return

    # Store time and move to city input
    await state.update_data(birth_time=time(hour, minute))
    await state.set_state(BirthDataStates.waiting_birth_city)

    await message.answer(
        f"Время рождения: {hour:02d}:{minute:02d}\n\n"
        "Теперь введите город рождения (на русском или английском):"
    )


@router.message(BirthDataStates.waiting_birth_city)
async def process_birth_city(
    message: Message,
    state: FSMContext,
) -> None:
    """Search for city and show results."""
    query = message.text.strip()

    if len(query) < 2:
        await message.answer(
            "Введите хотя бы 2 символа для поиска города."
        )
        return

    # Search cities via geocoding
    cities = await search_city(query, max_results=5)

    if not cities:
        await message.answer(
            f"Город '{query}' не найден. Попробуйте другое название "
            "(например, на английском)."
        )
        return

    # Store cities in state for later selection
    await state.update_data(
        cities=[
            {
                "name": c.name,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "timezone": c.timezone,
            }
            for c in cities
        ]
    )
    await state.set_state(BirthDataStates.selecting_city)

    await message.answer(
        "Выберите город из списка:",
        reply_markup=build_city_selection_keyboard(cities),
    )


@router.callback_query(
    CitySelectCallback.filter(), BirthDataStates.selecting_city
)
async def select_city(
    callback: CallbackQuery,
    callback_data: CitySelectCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Handle city selection and save birth data."""
    await callback.answer()

    data = await state.get_data()
    cities = data.get("cities", [])
    idx = callback_data.idx

    if idx >= len(cities):
        await callback.message.edit_text(
            "Ошибка выбора города. Попробуйте начать заново."
        )
        await state.clear()
        return

    city = cities[idx]
    birth_time_value = data.get("birth_time")

    # Update user in database
    stmt = select(User).where(User.telegram_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.message.edit_text(
            "Профиль не найден. Нажмите /start для регистрации."
        )
        await state.clear()
        return

    user.birth_time = birth_time_value
    user.birth_city = city["name"]
    user.birth_lat = city["latitude"]
    user.birth_lon = city["longitude"]
    # Also update timezone for accurate natal chart calculations
    if city.get("timezone"):
        user.timezone = city["timezone"]
    await session.commit()

    await logger.ainfo(
        "birth_data_saved",
        user_id=user.telegram_id,
        birth_time=str(birth_time_value) if birth_time_value else "noon",
        birth_city=city["name"],
    )

    await state.clear()

    # Format success message
    time_str = (
        f"{birth_time_value.hour:02d}:{birth_time_value.minute:02d}"
        if birth_time_value
        else "не указано (12:00)"
    )

    await callback.message.edit_text(
        "Данные рождения сохранены!\n\n"
        f"Время: {time_str}\n"
        f"Город: {city['name']}\n\n"
        "Теперь ваши гороскопы будут учитывать натальную карту.",
        reply_markup=build_birth_data_complete_keyboard(),
    )


@router.callback_query(F.data == "retry_city_search", BirthDataStates.selecting_city)
async def retry_city_search(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Let user enter city name again."""
    await callback.answer()

    await state.set_state(BirthDataStates.waiting_birth_city)

    await callback.message.edit_text(
        "Введите название города ещё раз (на русском или английском):"
    )


@router.callback_query(F.data == "cancel_birth_data")
async def cancel_birth_data(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Cancel birth data collection."""
    await callback.answer()
    await state.clear()

    await callback.message.edit_text(
        "Настройка натальной карты отменена.\n\n"
        "Вы можете вернуться к ней позже через профиль."
    )
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
