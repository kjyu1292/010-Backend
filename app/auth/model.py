"""----------------------------"""
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


"""----------------------------"""
class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length = 8, max_length = 72)
    display_name: str
    platform: str

    @field_validator("password")
    @classmethod
    def check_byte_length(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must be 72 bytes or fewer")
        return password


class TokenData(BaseModel):
    user_id: UUID


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPair(Token):
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str
