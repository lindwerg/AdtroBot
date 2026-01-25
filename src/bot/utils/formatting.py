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
    forecast_text: str,
    daily_tip: str,
    is_premium: bool = False,
) -> Text:
    """
    Format horoscope message using entity-based formatting.

    Output format:

        {emoji} {sign_name_ru} | {DD} {месяц_ru}

        *🔮 Общий прогноз*  (или *💎 Твой персональный прогноз* для premium)

        {forecast_text}

        *💡 Совет дня*

        > {tip_text}

    Args:
        sign_emoji: Zodiac emoji (e.g., "♈️")
        sign_name_ru: Russian name of the sign (e.g., "Овен")
        forecast_date: Date of the forecast
        forecast_text: Forecast text (general or personalized)
        daily_tip: 2 sentences actionable advice
        is_premium: Whether this is a personalized premium horoscope

    Returns:
        Text object with proper entities. Use: await message.answer(**content.as_kwargs())
    """
    date_str = f"{forecast_date.day} {MONTHS_RU[forecast_date.month]}"

    # Choose header based on premium status
    if is_premium:
        header = "💎 Твой персональный прогноз"
    else:
        header = "🔮 Общий прогноз"

    return Text(
        as_line(f"{sign_emoji} {sign_name_ru} | {date_str}"),
        "\n",
        Bold(header),
        "\n\n",
        as_line(forecast_text),
        "\n",
        Bold("💡 Совет дня"),
        "\n\n",
        BlockQuote(daily_tip),
    )
