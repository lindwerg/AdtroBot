from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.auth import create_access_token, get_current_admin, verify_password
from src.admin.models import Admin
from src.admin.schemas import AdminInfo, Token
from src.config import settings
from src.db.engine import get_session

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Token:
    """Authenticate admin and return JWT token."""
    result = await session.execute(
        select(Admin).where(Admin.username == form_data.username)
    )
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": admin.username},
        expires_delta=timedelta(minutes=settings.admin_jwt_expire_minutes),
    )
    return Token(access_token=access_token)


@admin_router.get("/me", response_model=AdminInfo)
async def get_me(current_admin: Admin = Depends(get_current_admin)) -> AdminInfo:
    """Get current admin info."""
    return AdminInfo.model_validate(current_admin)
