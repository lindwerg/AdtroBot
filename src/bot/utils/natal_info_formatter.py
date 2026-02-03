"""Форматирование натальной информации для главного меню."""

from src.db.models.user import User
from src.services.astrology.natal_chart import (
    FullNatalChartResult,
    HouseCusp,
    PlanetPosition,
)

# Глифы планет
PLANET_GLYPHS = {
    "sun": "☉",
    "moon": "☽",
    "mercury": "☿",
    "venus": "♀",
    "mars": "♂",
    "jupiter": "♃",
    "saturn": "♄",
    "uranus": "♅",
    "neptune": "♆",
    "pluto": "♇",
    "north_node": "☊",
}

# Русские названия планет
PLANET_NAMES_RU = {
    "sun": "Солнце",
    "moon": "Луна",
    "mercury": "Меркурий",
    "venus": "Венера",
    "mars": "Марс",
    "jupiter": "Юпитер",
    "saturn": "Сатурн",
    "uranus": "Уран",
    "neptune": "Нептун",
    "pluto": "Плутон",
    "north_node": "Сев. узел",
}

# Эмодзи для домов
HOUSE_EMOJIS = {
    1: "1️⃣",
    4: "4️⃣",
    7: "7️⃣",
    10: "🔟",
}

# Описания домов
HOUSE_DESCRIPTIONS = {
    1: "личность",
    4: "дом и семья",
    7: "партнёрство",
    10: "карьера",
}


def format_planet_position(planet_key: str, position: PlanetPosition) -> str:
    """Форматировать позицию планеты.

    Args:
        planet_key: Ключ планеты (например, "sun", "moon")
        position: Позиция планеты с долготой, знаком и градусом

    Returns:
        Строка вида "☉ Солнце в Льве 15°"
    """
    glyph = PLANET_GLYPHS.get(planet_key, "")
    name_ru = PLANET_NAMES_RU.get(planet_key, planet_key)
    sign_ru = position["sign_ru"]
    degree = position["degree"]

    return f"{glyph} {name_ru} в {sign_ru} {degree:.0f}°"


def format_planet_position_with_meaning(
    planet_key: str, position: PlanetPosition, meaning: str
) -> str:
    """Форматировать позицию планеты с описанием значения.

    Args:
        planet_key: Ключ планеты
        position: Позиция планеты
        meaning: Описание значения (например, "ваша суть")

    Returns:
        Строка вида "☉ Солнце в Льве 15° — ваша суть"
    """
    base = format_planet_position(planet_key, position)
    return f"{base} — {meaning}"


def format_house(house_num: int, cusp: HouseCusp) -> str:
    """Форматировать дом с описанием.

    Args:
        house_num: Номер дома (1-12)
        cusp: Куспид дома с знаком

    Returns:
        Строка вида "1️⃣ дом в Скорпионе — личность"
    """
    emoji = HOUSE_EMOJIS.get(house_num, f"{house_num}")
    sign_ru = cusp["sign_ru"]
    description = HOUSE_DESCRIPTIONS.get(house_num, "")

    if description:
        return f"{emoji} дом в {sign_ru} — {description}"
    return f"{emoji} дом в {sign_ru}"


def format_natal_info_for_menu(user: User, natal_data: FullNatalChartResult | None) -> str:
    """Форматировать натальную информацию для главного меню.

    Args:
        user: Пользователь
        natal_data: Полная натальная карта (или None)

    Returns:
        Форматированный текст с информацией для главного меню
    """
    # Free пользователь — тизер премиум-функций
    if not user.is_premium:
        return _format_free_teaser()

    # Premium без натальных данных — предложение заполнить
    if natal_data is None:
        return _format_premium_no_data_message()

    # Premium с натальными данными — показать информацию
    return _format_premium_natal_info(natal_data)


def _format_free_teaser() -> str:
    """Тизер премиум-функций для бесплатных пользователей."""
    return """✨ В Premium версии доступно:
• Персональный гороскоп по натальной карте
• Детальные прогнозы: любовь, карьера, финансы
• Позиции всех планет в вашей карте
• Расшифровка 12 домов натальной карты
• 20 раскладов таро в день
• Кельтский крест (10 карт)

Попробуйте Premium и откройте все возможности астрологии! 👇"""


def _format_premium_no_data_message() -> str:
    """Сообщение для Premium пользователей без натальных данных."""
    return """🔮 Заполните натальные данные для получения персонального прогноза!

После заполнения даты, времени и места рождения вы получите:
• Позиции всех планет в вашей карте
• Расшифровку 12 домов
• Персональные прогнозы на каждый день
• Детальные интерпретации

Перейдите в раздел 'Натальная карта' для настройки 👇"""


def _format_premium_natal_info(natal_data: FullNatalChartResult) -> str:
    """Форматировать натальную информацию для Premium пользователей.

    Показывает:
    - Основу личности (Солнце, Луна, Асцендент)
    - Личные планеты (Меркурий, Венера, Марс)
    - Ключевые дома (1, 4, 7, 10)

    Args:
        natal_data: Полная натальная карта

    Returns:
        Форматированный текст с натальной информацией
    """
    planets = natal_data["planets"]
    houses = natal_data["houses"]
    angles = natal_data.get("angles", {})
    ascendant = angles.get("ascendant")  # Может быть None если время неизвестно

    lines = ["🌟 Ваш астрологический профиль", ""]

    # Основа личности (3 точки)
    lines.append("💫 Основа личности:")
    lines.append(format_planet_position_with_meaning("sun", planets["sun"], "ваша суть"))
    lines.append(format_planet_position_with_meaning("moon", planets["moon"], "ваши эмоции"))

    # Асцендент (если известен)
    if ascendant:
        asc_text = f"↗ Асцендент в {ascendant['sign_ru']} {ascendant['degree']:.0f}° — ваш образ"
        lines.append(asc_text)

    lines.append("")

    # Личные планеты (3 планеты)
    lines.append("🎯 Личные планеты:")
    lines.append(
        format_planet_position_with_meaning("mercury", planets["mercury"], "ваше мышление")
    )
    lines.append(format_planet_position_with_meaning("venus", planets["venus"], "ваша любовь"))
    lines.append(format_planet_position_with_meaning("mars", planets["mars"], "ваша энергия"))

    lines.append("")

    # Ключевые дома (4 дома)
    lines.append("🏛️ Ключевые дома:")
    for house_num in [1, 4, 7, 10]:
        if house_num in houses:
            lines.append(format_house(house_num, houses[house_num]))

    lines.append("")
    lines.append('Полная информация в разделе "Натальная карта" 📊')

    return "\n".join(lines)
