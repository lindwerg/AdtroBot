"""Tarot message formatting with entity-based approach."""

from aiogram.utils.formatting import BlockQuote, Bold, Text


# Russian card type names
CARD_TYPE_RU = {
    "major": "Старший Аркан",
    "minor": "Младший Аркан",
}

# Position names for 3-card spread (Past, Present, Future)
SPREAD_POSITIONS = ["Прошлое", "Настоящее", "Будущее"]


def format_card_of_day(card: dict, reversed_flag: bool) -> Text:
    """
    Format Card of the Day message.

    Output:
        *Карта дня*

        *{card_name}* (перевернутая)
        {card_type}

        *Значение:*
        > {meaning}
    """
    card_name = card["name"]
    card_type = CARD_TYPE_RU.get(card["type"], card["type"])
    meaning = card["meaning_rev"] if reversed_flag else card["meaning_up"]
    reversed_text = " (перевернутая)" if reversed_flag else ""

    return Text(
        Bold("Карта дня"),
        "\n\n",
        Bold(f"{card_name}{reversed_text}"),
        "\n",
        card_type,
        "\n\n",
        Bold("Значение:"),
        "\n",
        BlockQuote(meaning),
    )


def format_three_card_spread(
    cards: list[tuple[dict, bool]],
    question: str,
) -> Text:
    """
    Format 3-card spread message (Past, Present, Future).

    Output:
        *Ваш вопрос:*
        > {question}

        *Прошлое:* {card1} (перевернутая)
        > {meaning1}

        *Настоящее:* {card2}
        > {meaning2}

        *Будущее:* {card3}
        > {meaning3}
    """
    content: list = [
        Bold("Ваш вопрос:"),
        "\n",
        BlockQuote(question),
        "\n\n",
    ]

    for i, (card, reversed_flag) in enumerate(cards):
        position = SPREAD_POSITIONS[i]
        card_name = card["name"]
        meaning = card["meaning_rev"] if reversed_flag else card["meaning_up"]
        reversed_text = " (перевернутая)" if reversed_flag else ""

        content.extend(
            [
                Bold(f"{position}:"),
                f" {card_name}{reversed_text}",
                "\n",
                BlockQuote(meaning),
                "\n\n",
            ]
        )

    return Text(*content)


def format_limit_message(remaining: int, is_premium: bool = False) -> str:
    """Format remaining spreads message."""
    limit = 20 if is_premium else 1
    return f"Раскладов на сегодня: {remaining}/{limit}"


def format_limit_exceeded() -> Text:
    """Format limit exceeded message with premium teaser."""
    return Text(
        Bold("Дневной лимит исчерпан"),
        "\n\n",
        "Вы уже сделали расклад сегодня. ",
        "Приходите завтра или оформите Premium!",
        "\n\n",
        Bold("Premium:"),
        " 20 раскладов в день",
    )


# ============== AI-powered formatting ==============

AI_FALLBACK_MESSAGE = "Сервис интерпретации временно недоступен. Попробуй позже."


def format_ai_interpretation(interpretation: str) -> Text:
    """Format AI-generated interpretation text.

    AI text comes with [SECTION] headers that need to be displayed nicely.
    """
    return Text(
        Bold("Интерпретация:"),
        "\n\n",
        interpretation,
    )


def format_card_of_day_with_ai(
    card: dict, reversed_flag: bool, ai_interpretation: str | None
) -> Text:
    """Format Card of the Day with AI interpretation.

    If AI interpretation available, show it instead of static meaning.
    """
    card_name = card["name"]
    card_type = CARD_TYPE_RU.get(card["type"], card["type"])
    reversed_text = " (перевернутая)" if reversed_flag else ""

    parts: list = [
        Bold("Карта дня"),
        "\n\n",
        Bold(f"{card_name}{reversed_text}"),
        "\n",
        card_type,
        "\n\n",
    ]

    if ai_interpretation:
        parts.append(ai_interpretation)
    else:
        # Fallback to static meaning
        meaning = card["meaning_rev"] if reversed_flag else card["meaning_up"]
        parts.extend(
            [
                Bold("Значение:"),
                "\n",
                BlockQuote(meaning),
            ]
        )

    return Text(*parts)


def format_three_card_spread_with_ai(
    cards: list[tuple[dict, bool]],
    question: str,
    ai_interpretation: str | None,
) -> Text:
    """Format 3-card spread with AI interpretation.

    If AI interpretation available, show question + cards + AI text.
    Otherwise fallback to static meanings.
    """
    content: list = [
        Bold("Ваш вопрос:"),
        "\n",
        BlockQuote(question),
        "\n\n",
    ]

    # Show cards with names
    content.append(Bold("Карты расклада:"))
    content.append("\n")
    for i, (card, reversed_flag) in enumerate(cards):
        position = SPREAD_POSITIONS[i]
        card_name = card["name"]
        reversed_text = " (перевернутая)" if reversed_flag else ""
        content.append(f"{position}: {card_name}{reversed_text}\n")

    content.append("\n")

    if ai_interpretation:
        content.append(ai_interpretation)
    else:
        # Fallback to static meanings (same as original format_three_card_spread)
        for i, (card, reversed_flag) in enumerate(cards):
            position = SPREAD_POSITIONS[i]
            meaning = card["meaning_rev"] if reversed_flag else card["meaning_up"]
            content.extend(
                [
                    Bold(f"{position}:"),
                    "\n",
                    BlockQuote(meaning),
                    "\n\n",
                ]
            )

    return Text(*content)
