"""Image asset service with Telegram file_id caching."""

import random
from pathlib import Path

import structlog
from aiogram import Bot
from aiogram.types import FSInputFile, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.image_asset import ImageAsset

logger = structlog.get_logger()

# Path to cosmic images directory
COSMIC_IMAGES_DIR = Path("assets/images/cosmic")


class ImageAssetService:
    """Service for sending images with file_id caching.

    Features:
    - First send: uploads file via FSInputFile, caches file_id in PostgreSQL
    - Subsequent sends: uses cached file_id for instant delivery
    - Random cosmic image selection for visual variety
    """

    _instance: "ImageAssetService | None" = None
    _cosmic_images: list[str]

    def __init__(self) -> None:
        """Initialize and load cosmic image paths."""
        self._cosmic_images = []
        self._load_cosmic_images()

    def _load_cosmic_images(self) -> None:
        """Load list of cosmic image filenames."""
        if COSMIC_IMAGES_DIR.exists():
            self._cosmic_images = [f.name for f in COSMIC_IMAGES_DIR.glob("*.jpg")]
            logger.info("cosmic_images_loaded", count=len(self._cosmic_images))
        else:
            self._cosmic_images = []
            logger.warning("cosmic_images_dir_not_found", path=str(COSMIC_IMAGES_DIR))

    def get_random_cosmic_key(self) -> str | None:
        """Get random cosmic image asset key.

        Returns:
            Asset key like "cosmic/pexels-xxx.jpg" or None if no images
        """
        if not self._cosmic_images:
            return None
        filename = random.choice(self._cosmic_images)
        return f"cosmic/{filename}"

    async def send_image(
        self,
        bot: Bot,
        chat_id: int,
        asset_key: str,
        session: AsyncSession,
        caption: str | None = None,
        reply_markup=None,
    ) -> Message | None:
        """Send image using cached file_id or upload and cache.

        Args:
            bot: Telegram Bot instance
            chat_id: Target chat ID
            asset_key: Unique key (e.g., "cosmic/pexels-abc.jpg")
            session: Database session
            caption: Optional photo caption
            reply_markup: Optional keyboard

        Returns:
            Sent Message or None on error
        """
        # Check cache
        stmt = select(ImageAsset).where(ImageAsset.asset_key == asset_key)
        result = await session.execute(stmt)
        cached = result.scalar_one_or_none()

        if cached:
            # Cache hit - send by file_id (instant)
            logger.debug("image_cache_hit", asset_key=asset_key)
            try:
                return await bot.send_photo(
                    chat_id=chat_id,
                    photo=cached.file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                )
            except Exception as e:
                # file_id might be invalid (e.g., different bot)
                logger.warning(
                    "image_cache_send_failed",
                    asset_key=asset_key,
                    error=str(e),
                )
                # Fall through to upload

        # Cache miss or failed - upload file and cache file_id
        file_path = Path("assets/images") / asset_key
        if not file_path.exists():
            logger.warning("image_file_not_found", path=str(file_path))
            return None

        logger.debug("image_cache_miss", asset_key=asset_key)

        try:
            message = await bot.send_photo(
                chat_id=chat_id,
                photo=FSInputFile(file_path),
                caption=caption,
                reply_markup=reply_markup,
            )

            # Extract file_id from response and cache
            if message.photo:
                file_id = message.photo[-1].file_id  # Largest size

                # Update or create cache entry
                if cached:
                    cached.file_id = file_id
                else:
                    asset = ImageAsset(
                        asset_key=asset_key,
                        file_id=file_id,
                    )
                    session.add(asset)

                await session.commit()
                logger.info("image_cached", asset_key=asset_key)

            return message

        except Exception as e:
            logger.error("image_send_failed", asset_key=asset_key, error=str(e))
            return None

    async def send_random_cosmic(
        self,
        bot: Bot,
        chat_id: int,
        session: AsyncSession,
        caption: str | None = None,
        reply_markup=None,
    ) -> Message | None:
        """Send random cosmic image.

        Args:
            bot: Telegram Bot instance
            chat_id: Target chat ID
            session: Database session
            caption: Optional photo caption
            reply_markup: Optional keyboard

        Returns:
            Sent Message or None if no images available
        """
        asset_key = self.get_random_cosmic_key()
        if not asset_key:
            logger.warning("no_cosmic_images_available")
            return None

        return await self.send_image(
            bot=bot,
            chat_id=chat_id,
            asset_key=asset_key,
            session=session,
            caption=caption,
            reply_markup=reply_markup,
        )


# Singleton
_instance: ImageAssetService | None = None


def get_image_asset_service() -> ImageAssetService:
    """Get image asset service singleton.

    Returns:
        ImageAssetService instance
    """
    global _instance
    if _instance is None:
        _instance = ImageAssetService()
    return _instance
