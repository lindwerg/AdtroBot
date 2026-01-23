import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/adtrobot",
        validation_alias="DATABASE_URL",
    )

    # App
    debug: bool = False
    log_level: str = "INFO"

    # Server
    port: int = 8000

    # Railway auto-injected
    railway_environment: str | None = None

    # Telegram
    telegram_bot_token: str = Field(
        default="",
        validation_alias="TELEGRAM_BOT_TOKEN",
    )
    webhook_base_url: str = Field(
        default="",
        validation_alias="WEBHOOK_BASE_URL",
    )
    webhook_secret: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
    )

    # OpenRouter
    openrouter_api_key: str = Field(
        default="",
        validation_alias="OPENROUTER_API_KEY",
    )

    # YooKassa
    yookassa_shop_id: str = Field(
        default="",
        validation_alias="YOOKASSA_SHOP_ID",
    )
    yookassa_secret_key: str = Field(
        default="",
        validation_alias="YOOKASSA_SECRET_KEY",
    )
    yookassa_return_url: str = Field(
        default="https://t.me/AdtroBot",  # Return to bot after payment
        validation_alias="YOOKASSA_RETURN_URL",
    )

    @property
    def async_database_url(self) -> str:
        """Convert postgresql:// to postgresql+asyncpg:// if needed."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Get sync database URL (without asyncpg)."""
        url = self.database_url
        if "+asyncpg" in url:
            url = url.replace("+asyncpg", "")
        if url.startswith("postgresql://"):
            return url
        return url.replace("postgresql+asyncpg://", "postgresql://")


settings = Settings()
