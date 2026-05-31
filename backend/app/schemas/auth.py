"""Authentication schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    tenant_name: str = Field(min_length=2, max_length=255)
    role: str = Field(default="admin", pattern="^(analyst|lead|admin|readonly)$")


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    tenant_id: UUID

    model_config = {"from_attributes": True}
