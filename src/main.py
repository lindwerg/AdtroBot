from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.core.logging import configure_logging
from src.db.engine import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup: configure logging
    configure_logging(
        log_level=settings.log_level,
        json_logs=settings.railway_environment is not None,
    )
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
