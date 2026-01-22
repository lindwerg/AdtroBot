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

    @property
    def async_database_url(self) -> str:
        """Convert postgresql:// to postgresql+asyncpg:// if needed."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
