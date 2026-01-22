"""Entity-based message formatting utilities."""

from datetime import date

from aiogram.utils.formatting import BlockQuote, Bold, Text, as_line


# Russian month names (genitive case for dates)
MONTHS_RU = (
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def format_daily_horoscope(
    sign_emoji: str,
    sign_name_ru: str,
    forecast_date: date,
    general_forecast: str,
    daily_tip: str,
) -> Text:
    """
    Format horoscope message using entity-based formatting.

    Output format (from CONTEXT.md):

        {emoji} {sign_name_ru} | {DD} {месяц_ru}

        *🔮 Общий прогноз*

        {forecast_text}

        *💡 Совет дня*

        > {tip_text}

    Args:
        sign_emoji: Zodiac emoji (e.g., "♈️")
        sign_name_ru: Russian name of the sign (e.g., "Овен")
        forecast_date: Date of the forecast
        general_forecast: 4-5 sentences general forecast
        daily_tip: 2 sentences actionable advice

    Returns:
        Text object with proper entities. Use: await message.answer(**content.as_kwargs())
    """
    date_str = f"{forecast_date.day} {MONTHS_RU[forecast_date.month]}"

    return Text(
        as_line(f"{sign_emoji} {sign_name_ru} | {date_str}"),
        "\n",
        Bold("🔮 Общий прогноз"),
        "\n\n",
        as_line(general_forecast),
        "\n",
        Bold("💡 Совет дня"),
        "\n\n",
        BlockQuote(daily_tip),
    )
