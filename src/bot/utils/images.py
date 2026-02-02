"""Image utilities for Astraro bot."""
import structlog
from pathlib import Path

from aiogram.types import FSInputFile

logger = structlog.get_logger()

# Base path for images - handle both local and Docker paths
IMAGES_DIR = Path(__file__).parent.parent.parent / "data" / "images"


def get_image(name: str) -> FSInputFile | None:
    """Get image file by name.
    
    Args:
        name: Image name without extension (e.g., 'welcome', 'horoscope')
        
    Returns:
        FSInputFile for sending via aiogram, or None if not found
    """
    try:
        path = IMAGES_DIR / f"{name}.png"
        if path.exists():
            return FSInputFile(path)
        logger.warning("Image not found", name=name, path=str(path))
        return None
    except Exception as e:
        logger.error("Error loading image", name=name, error=str(e))
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
