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
