"""Birth data callbacks."""

from aiogram.filters.callback_data import CallbackData


class CitySelectCallback(CallbackData, prefix="bcity"):
    """Callback for city selection from geocoding results."""

    idx: int  # Index in results list (0-4)


class SkipTimeCallback(CallbackData, prefix="bskip"):
    """Callback for skipping birth time input."""

    pass
