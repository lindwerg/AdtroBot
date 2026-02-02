"""Image utilities for Astraro bot."""
from pathlib import Path

from aiogram.types import FSInputFile

# Base path for images
IMAGES_DIR = Path(__file__).parent.parent.parent / "data" / "images"


def get_image(name: str) -> FSInputFile | None:
    """Get image file by name.
    
    Args:
        name: Image name without extension (e.g., 'welcome', 'horoscope')
        
    Returns:
        FSInputFile for sending via aiogram, or None if not found
    """
    path = IMAGES_DIR / f"{name}.png"
    if path.exists():
        return FSInputFile(path)
    return None


# Pre-defined image names
class BotImages:
    """Available bot images."""
    WELCOME = "welcome"
    HOROSCOPE = "horoscope"
    TAROT_MENU = "tarot_menu"
    PROFILE = "profile"
    SUBSCRIPTION = "subscription"
    NATAL = "natal"
