"""Image asset model for Telegram file_id caching."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class ImageAsset(Base):
    """Cached Telegram file_ids for images.

    After first upload, file_id is stored for instant re-sending.
    This eliminates repeated file uploads to Telegram servers.
    """

    __tablename__ = "image_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Unique key for the asset (e.g., "cosmic/pexels-abc-123.jpg")
    asset_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Telegram file_id (returned after first upload)
    file_id: Mapped[str] = mapped_column(String(255))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
    )

    def __repr__(self) -> str:
        return f"<ImageAsset(key={self.asset_key})>"
