from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str = "bearer"


class AdminInfo(BaseModel):
    """Admin info response schema."""

    id: int
    username: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
