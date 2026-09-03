"""----------------------------"""
from uuid import UUID
from pydantic import BaseModel, Field


"""----------------------------"""
class PlayerProfileResponse(BaseModel):
    user_id: UUID
    level: int
    xp: int
    soft_currency: int
    hard_currency: int
    avatar_id: str | None = None

    class Config:
        from_attributes = True


class PlayerProfileUpdate(BaseModel):
    # The ONLY client-writable field.
    # Other fields must only ever change server-side, via gameplay
    # endpoints (level completion, purchases) -- never direct client PATCH,
    # or a client can just set its own currency to 999999.
    avatar_id: str | None = Field(default=None, max_length=64)
