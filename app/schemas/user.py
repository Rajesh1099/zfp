
import re

from pydantic import BaseModel, EmailStr, field_validator

from app.core.roles import UserRole


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError(
            "Password must be at least 8 characters long"
        )

    if not re.search(r"[A-Z]", password):
        raise ValueError(
            "Password must contain at least one uppercase letter"
        )

    if not re.search(r"[a-z]", password):
        raise ValueError(
            "Password must contain at least one lowercase letter"
        )

    if not re.search(r"\d", password):
        raise ValueError(
            "Password must contain at least one number"
        )

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\\/\[\];'+=`~]", password):
        raise ValueError(
            "Password must contain at least one special character"
        )

    return password


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password_strength(password)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, password: str) -> str:
        return validate_password_strength(password)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, password: str) -> str:
        return validate_password_strength(password)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    active: bool
