"""Tarot message formatting with entity-based approach."""


from aiogram.utils.formatting import BlockQuote, Bold, Text


# Russian card type names
CARD_TYPE_RU = {
    "major": "Старший Аркан",
    "minor": "Младший Аркан",
}

# Position names for 3-card spread (Past, Present, Future)
SPREAD_POSITIONS = ["Прошлое", "Настоящее", "Будущее"]

# Position names for Celtic Cross spread
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


# ============== Celtic Cross formatting ==============


def format_celtic_cross_with_ai(
    cards: list[tuple[dict, bool]],
    question: str,
    ai_interpretation: str | None,
) -> Text:
    """Format Celtic Cross 10-card spread with AI interpretation.

    If AI interpretation available, show question + cards + AI text.
    Otherwise fallback to static meanings.
    """
    content: list = [
        Bold("Кельтский крест"),
        "\n\n",
        Bold("Ваш вопрос:"),
        "\n",
        BlockQuote(question),
        "\n\n",
    ]

    # Show cards with positions
    content.append(Bold("Карты расклада:"))
    content.append("\n")
    for i, (card, reversed_flag) in enumerate(cards):
        position = CELTIC_CROSS_POSITIONS[i]
        card_name = card["name"]
        reversed_text = " (перевернутая)" if reversed_flag else ""
        content.append(f"{i + 1}. {position}: {card_name}{reversed_text}\n")

    content.append("\n")

    if ai_interpretation:
        content.append(ai_interpretation)
    else:
        # Fallback to static meanings
        for i, (card, reversed_flag) in enumerate(cards):
            position = CELTIC_CROSS_POSITIONS[i]
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


# ============== History formatting ==============


def format_history_item(spread) -> str:
    """Format a single history item for list display.

    Args:
        spread: TarotSpread object

    Returns:
        Formatted string: "23.01 [CC] Вопрос про любовь..."
    """
    date_str = spread.created_at.strftime("%d.%m")
    type_label = "CC" if spread.spread_type == "celtic_cross" else "3K"
    question_preview = (
        spread.question[:25] + "..." if len(spread.question) > 25 else spread.question
    )
    return f"{date_str} [{type_label}] {question_preview}"


def format_spread_detail(spread, cards_data: list[dict]) -> Text:
    """Format spread detail view from history.

    Args:
        spread: TarotSpread object with cards JSON
        cards_data: List of card dicts from get_card_by_id

    Returns:
        Formatted Text with cards and interpretation
    """
    # Determine positions based on spread type
    if spread.spread_type == "celtic_cross":
        positions = CELTIC_CROSS_POSITIONS
        title = "Кельтский крест"
    else:
        positions = SPREAD_POSITIONS
        title = "Расклад на 3 карты"

    date_str = spread.created_at.strftime("%d.%m.%Y %H:%M")

    content: list = [
        Bold(title),
        f"\n{date_str}\n\n",
        Bold("Ваш вопрос:"),
        "\n",
        BlockQuote(spread.question),
        "\n\n",
        Bold("Карты:"),
        "\n",
    ]

    # Show cards
    for i, card_info in enumerate(spread.cards):
        card_id = card_info.get("card_id")
        reversed_flag = card_info.get("reversed", False)

        # Find card in cards_data
        card = None
        for c in cards_data:
            if c["name_short"] == card_id:
                card = c
                break

        if card:
            card_name = card["name"]
        else:
            card_name = card_id or "Неизвестная карта"

        reversed_text = " (перевернутая)" if reversed_flag else ""
        position = positions[i] if i < len(positions) else f"Карта {i + 1}"
        content.append(f"{i + 1}. {position}: {card_name}{reversed_text}\n")

    content.append("\n")

    # Show stored interpretation
    if spread.interpretation:
        content.append(spread.interpretation)
    else:
        content.append("Интерпретация недоступна.")

    return Text(*content)
