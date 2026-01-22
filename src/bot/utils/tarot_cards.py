"""Tarot card utilities: deck loading, random selection, image handling."""

import json
import random
from io import BytesIO
from pathlib import Path

from PIL import Image
from aiogram.types import BufferedInputFile, FSInputFile


def load_tarot_deck() -> list[dict]:
    """Load 78 tarot cards from JSON."""
    deck_path = Path(__file__).parent.parent.parent / "data" / "tarot" / "cards.json"
    with open(deck_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cards"]


# Singleton deck (loaded once)
_DECK: list[dict] | None = None


def get_deck() -> list[dict]:
    """Get tarot deck (lazy load singleton)."""
    global _DECK
    if _DECK is None:
        _DECK = load_tarot_deck()
    return _DECK


def get_random_card() -> tuple[dict, bool]:
    """
    Return random card + reversed flag (50% chance).

    Returns:
        (card_dict, is_reversed)
    """
    deck = get_deck()
    card = random.choice(deck)
    reversed_flag = random.choice([True, False])
    return card, reversed_flag


def get_three_cards() -> list[tuple[dict, bool]]:
    """
    Return 3 unique cards with reversed flags.

    Uses random.sample() to guarantee uniqueness.
    """
    deck = get_deck()
    cards = random.sample(deck, 3)
    return [(card, random.choice([True, False])) for card in cards]


def get_card_by_id(name_short: str) -> dict | None:
    """Get card by name_short (e.g., 'ar00')."""
    deck = get_deck()
    for card in deck:
        if card["name_short"] == name_short:
            return card
    return None


def get_card_image(
    name_short: str, reversed_flag: bool = False
) -> BufferedInputFile | FSInputFile:
    """
    Get card image for sending to Telegram.

    Args:
        name_short: Card ID (e.g., "ar00")
        reversed_flag: If True, rotate image 180 degrees

    Returns:
        BufferedInputFile (rotated) or FSInputFile (upright)
    """
    image_path = (
        Path(__file__).parent.parent.parent / "data" / "tarot" / "images" / f"{name_short}.jpg"
    )

    if not reversed_flag:
        # Upright card - send directly
        return FSInputFile(image_path)

    # Reversed - rotate 180 degrees via Pillow
    img = Image.open(image_path)
    rotated = img.transpose(Image.Transpose.ROTATE_180)
    buffer = BytesIO()
    rotated.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)

    return BufferedInputFile(buffer.read(), filename=f"{name_short}_reversed.jpg")
