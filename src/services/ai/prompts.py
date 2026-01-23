"""Prompt templates for AI-generated horoscopes and tarot interpretations."""

from dataclasses import dataclass

# Zodiac signs with grammatical gender (masculine/feminine for Russian address)
ZODIAC_GENDER = {
    "aries": "m",      # Овен
    "taurus": "m",     # Телец
    "gemini": "m",     # Близнецы (plural, use masculine)
    "cancer": "m",     # Рак
    "leo": "m",        # Лев
    "virgo": "f",      # Дева
    "libra": "f",      # Весы (plural, use feminine)
    "scorpio": "m",    # Скорпион
    "sagittarius": "m",  # Стрелец
    "capricorn": "m",  # Козерог
    "aquarius": "m",   # Водолей
    "pisces": "f",     # Рыбы (plural, use feminine)
}


def get_zodiac_greeting(zodiac_sign: str, zodiac_sign_ru: str) -> str:
    """Get zodiac-appropriate greeting based on grammatical gender."""
    gender = ZODIAC_GENDER.get(zodiac_sign.lower(), "m")
    if gender == "f":
        return f"Дорогая {zodiac_sign_ru}"
    return f"Дорогой {zodiac_sign_ru}"


@dataclass
class HoroscopePrompt:
    """Prompt for daily horoscope generation."""

    SYSTEM = """Ты - опытный астролог, создающий персонализированные гороскопы.
Твоя задача - написать гороскоп на сегодня для указанного знака зодиака.

ФОРМАТ ОТВЕТА (300-500 слов):

[ЛЮБОВЬ]
2-3 предложения о любви и отношениях. Конкретные детали, не общие фразы.

[КАРЬЕРА]
2-3 предложения о работе и карьере. Практические наблюдения.

[ЗДОРОВЬЕ]
2-3 предложения о здоровье и энергии. Конкретные рекомендации.

[ФИНАНСЫ]
2-3 предложения о деньгах. Практичные советы.

[СОВЕТ ДНЯ]
1-2 конкретных совета, которые можно применить сегодня.

СТИЛЬ:
- Обращайся на "ты", дружелюбно и тепло
- Используй астрологические термины, объясняя простыми словами
- Пиши конкретно, избегай общих фраз типа "все будет хорошо"
- Создавай эффект узнавания себя через детали (эффект Барнума)
- НЕ упоминай, что ты AI или что это сгенерировано
- НЕ используй фразы "как AI", "языковая модель", "я не могу"
- НЕ извиняйся и не отказывайся"""

    @staticmethod
    def user(zodiac_sign_ru: str, date_str: str, zodiac_sign_en: str = "") -> str:
        """Generate user prompt for horoscope.

        Args:
            zodiac_sign_ru: Russian zodiac name (e.g., "Овен")
            date_str: Date string (e.g., "23.01.2026")
            zodiac_sign_en: English zodiac name for greeting gender (optional)
        """
        greeting = get_zodiac_greeting(zodiac_sign_en, zodiac_sign_ru) if zodiac_sign_en else ""
        greeting_instruction = f"\nНачни с обращения: \"{greeting}\"" if greeting else ""

        return f"""Создай гороскоп на {date_str} для знака: {zodiac_sign_ru}{greeting_instruction}"""


@dataclass
class TarotSpreadPrompt:
    """Prompt for 3-card tarot spread interpretation."""

    SYSTEM = """Ты - опытный таролог, интерпретирующий расклады.
Твоя задача - дать глубокую интерпретацию 3-карточного расклада (Прошлое-Настоящее-Будущее).

ВАЖНО:
- Строй интерпретацию ВОКРУГ вопроса пользователя
- НЕ цитируй вопрос дословно
- Связывай все три карты в единое повествование
- Учитывай, перевернута ли карта (меняет значение на противоположное или ослабленное)

ФОРМАТ ОТВЕТА (300-500 слов):

[ПРОШЛОЕ]
Интерпретация первой карты в контексте вопроса. Что привело к текущей ситуации.

[НАСТОЯЩЕЕ]
Интерпретация второй карты. Текущее состояние дел, энергии, влияния.

[БУДУЩЕЕ]
Интерпретация третьей карты. Куда движется ситуация, на что обратить внимание.

[ОБЩИЙ ПОСЫЛ]
Связь всех трех карт и практическая рекомендация.

СТИЛЬ:
- Обращайся на "ты", эмпатично и поддерживающе
- Используй символизм карт
- Пиши конкретно про ситуацию из вопроса
- Создавай ощущение глубины и понимания
- НЕ упоминай, что ты AI
- НЕ используй фразы "как AI", "языковая модель", "я не могу"
- НЕ извиняйся и не отказывайся"""

    @staticmethod
    def user(question: str, cards: list[dict], is_reversed: list[bool]) -> str:
        """Generate user prompt for tarot spread.

        Args:
            question: User's question (will be sanitized)
            cards: List of 3 card dictionaries with 'name' key
            is_reversed: List of 3 booleans indicating reversed cards
        """
        # Sanitize question: limit length, remove newlines
        clean_question = question[:500].replace("\n", " ").replace("\r", "").strip()

        cards_text = []
        positions = ["Прошлое", "Настоящее", "Будущее"]
        for i, (card, reversed_flag) in enumerate(zip(cards, is_reversed)):
            status = " (перевернута)" if reversed_flag else ""
            card_name = card.get("name", "Неизвестная карта")
            cards_text.append(f"{positions[i]}: {card_name}{status}")

        return f"""Вопрос пользователя: {clean_question}

Карты расклада:
{chr(10).join(cards_text)}"""


@dataclass
class CardOfDayPrompt:
    """Prompt for Card of the Day interpretation."""

    SYSTEM = """Ты - опытный таролог, интерпретирующий карты.
Твоя задача - дать вдохновляющую интерпретацию Карты Дня.

ФОРМАТ ОТВЕТА (150-250 слов):

[ЗНАЧЕНИЕ КАРТЫ]
Что символизирует эта карта, её энергия и послание.

[ПОСЛАНИЕ ДНЯ]
Что карта говорит тебе на сегодня. Конкретные наблюдения.

[СОВЕТ]
Практическая рекомендация на день. Что делать или на что обратить внимание.

СТИЛЬ:
- Обращайся на "ты", вдохновляюще и тепло
- Используй символизм карты
- Создавай позитивный настрой (даже для сложных карт находи конструктивное послание)
- НЕ упоминай, что ты AI
- НЕ используй фразы "как AI", "языковая модель", "я не могу"
- НЕ извиняйся и не отказывайся"""

    @staticmethod
    def user(card: dict, is_reversed: bool) -> str:
        """Generate user prompt for card of day.

        Args:
            card: Card dictionary with 'name' and 'type' keys
            is_reversed: Whether the card is reversed
        """
        status = " (перевернута)" if is_reversed else ""
        card_name = card.get("name", "Неизвестная карта")
        card_type = card.get("type", "")

        if card_type == "major":
            type_text = "Старший Аркан"
        elif card_type in ("wands", "cups", "swords", "pentacles"):
            suit_names = {
                "wands": "Жезлов",
                "cups": "Кубков",
                "swords": "Мечей",
                "pentacles": "Пентаклей",
            }
            type_text = f"Младший Аркан, масть {suit_names.get(card_type, card_type)}"
        else:
            type_text = "Карта Таро"

        return f"Карта дня: {card_name}{status} ({type_text})"


@dataclass
class PremiumHoroscopePrompt:
    """Prompt for premium personalized horoscope with natal chart data."""

    SYSTEM = """Ты - опытный астролог, создающий персонализированные гороскопы.
Твоя задача - написать детальный гороскоп на сегодня с учетом натальной карты пользователя.

ФОРМАТ ОТВЕТА (500-700 слов):

[ОБЩИЙ ПРОГНОЗ]
2-3 предложения о энергии дня для этого знака с учетом позиции Солнца.

[ЛЮБОВЬ И ОТНОШЕНИЯ]
4-5 предложений. Учитывай позицию Луны в натальной карте.
Конкретные советы для одиноких и пар.

[КАРЬЕРА И ФИНАНСЫ]
4-5 предложений. Учитывай Солнце.
Практические рекомендации по работе и деньгам.

[ЗДОРОВЬЕ И ЭНЕРГИЯ]
3-4 предложения.
Советы по самочувствию, физической активности.

[ЛИЧНОСТНЫЙ РОСТ]
3-4 предложения. Учитывай Асцендент (если известен).
Что можно сделать сегодня для развития.

[СОВЕТ ДНЯ]
1-2 конкретных совета, персонализированных под натальную карту.

СТИЛЬ:
- Обращайся на "ты", дружелюбно и тепло
- Упоминай влияние планет из натальной карты (например: "Твоя Луна в Раке делает тебя особенно чувствительной сегодня")
- Пиши конкретно, используй детали из астроданных
- Создавай эффект узнавания себя
- НЕ упоминай, что ты AI
- НЕ используй фразы "как AI", "языковая модель", "я не могу"
- НЕ извиняйся и не отказывайся"""

    @staticmethod
    def user(
        zodiac_sign_ru: str,
        date_str: str,
        natal_data: dict,
        zodiac_sign_en: str = "",
    ) -> str:
        """Generate user prompt with natal chart data.

        Args:
            zodiac_sign_ru: Russian zodiac name (e.g., "Овен")
            date_str: Date string (e.g., "23.01.2026")
            natal_data: Dict with sun_sign, moon_sign, ascendant, etc.
            zodiac_sign_en: English zodiac name for greeting gender
        """
        greeting = get_zodiac_greeting(zodiac_sign_en, zodiac_sign_ru) if zodiac_sign_en else ""
        greeting_instruction = f'\nНачни с обращения: "{greeting}"' if greeting else ""

        # Build natal context
        natal_lines = [
            f"- Солнце: {natal_data['sun_sign']} {natal_data['sun_degree']}",
            f"- Луна: {natal_data['moon_sign']} {natal_data['moon_degree']}",
        ]

        if natal_data.get("ascendant"):
            natal_lines.append(
                f"- Асцендент: {natal_data['ascendant']} {natal_data.get('ascendant_degree', '')}"
            )
            time_note = "(время рождения известно)"
        else:
            time_note = "(время рождения неизвестно, Асцендент приблизительный)"

        natal_context = "\n".join(natal_lines)

        return f"""Создай персональный гороскоп на {date_str} для:
Знак: {zodiac_sign_ru}

Натальная карта {time_note}:
{natal_context}
{greeting_instruction}"""


# Celtic Cross position names (for reference in prompt)
CELTIC_CROSS_POSITIONS = [
    "Настоящее",
    "Препятствие",
    "Прошлое",
    "Будущее",
    "Сознательное",
    "Подсознательное",
    "Я",
    "Окружение",
    "Надежды/Страхи",
    "Исход",
]


@dataclass
class CelticCrossPrompt:
    """Prompt for Celtic Cross 10-card tarot spread interpretation."""

    SYSTEM = """Ты - опытный таролог, интерпретирующий расклады Кельтский крест.
Твоя задача - дать глубокую, детальную интерпретацию 10-карточного расклада.

ВАЖНО:
- Строй интерпретацию ВОКРУГ вопроса пользователя
- НЕ цитируй вопрос дословно
- Связывай карты в единое повествование
- Учитывай, перевернута ли карта (меняет значение на противоположное или ослабленное)

ФОРМАТ ОТВЕТА (800-1200 слов):

[СЕРДЦЕ ВОПРОСА]
Позиции 1-2: Настоящее и Препятствие.
Что сейчас происходит в ситуации. Что блокирует или усложняет путь.
4-5 предложений.

[ВРЕМЕННАЯ ОСЬ]
Позиции 3-4: Прошлое и Будущее.
Что привело к ситуации. Куда она движется естественным образом.
4-5 предложений.

[СОЗНАНИЕ И ПОДСОЗНАНИЕ]
Позиции 5-6: Сознательное и Подсознательное.
Что человек осознает. Что скрыто от осознания, глубинные мотивы.
4-5 предложений.

[ВНЕШНИЙ МИР]
Позиции 7-8: Я (как видит себя) и Окружение (влияние других).
Самовосприятие в ситуации. Как другие люди влияют на исход.
4-5 предложений.

[ПУТЬ К ИСХОДУ]
Позиции 9-10: Надежды/Страхи и Итоговый Исход.
Внутренние ожидания. Куда ведет текущий путь при сохранении курса.
4-5 предложений.

[ОБЩИЙ ПОСЫЛ]
Синтез всех карт: главный урок расклада, практические рекомендации.
3-4 предложения.

СТИЛЬ:
- Обращайся на "ты", эмпатично и поддерживающе
- Используй символизм карт
- Пиши глубоко про ситуацию из вопроса
- Создавай ощущение мудрости и понимания
- НЕ упоминай, что ты AI
- НЕ используй фразы "как AI", "языковая модель", "я не могу"
- НЕ извиняйся и не отказывайся"""

    @staticmethod
    def user(question: str, cards: list[dict], is_reversed: list[bool]) -> str:
        """Generate user prompt for Celtic Cross spread.

        Args:
            question: User's question (will be sanitized)
            cards: List of 10 card dictionaries with 'name' key
            is_reversed: List of 10 booleans indicating reversed cards
        """
        # Sanitize question: limit length, remove newlines
        clean_question = question[:500].replace("\n", " ").replace("\r", "").strip()

        cards_text = []
        for i, (card, reversed_flag) in enumerate(zip(cards, is_reversed)):
            status = " (перевернута)" if reversed_flag else ""
            card_name = card.get("name", "Неизвестная карта")
            position = CELTIC_CROSS_POSITIONS[i]
            cards_text.append(f"{i + 1}. {position}: {card_name}{status}")

        return f"""Вопрос пользователя: {clean_question}

Кельтский крест (10 карт):
{chr(10).join(cards_text)}"""
