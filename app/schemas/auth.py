"""
app/schemas/auth.py
────────────────────
Pydantic v2 schemas for auth endpoints.
Strong validation prevents injection & bad data.
"""
import re
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional


_NAME_RE = re.compile(r"^[A-Za-z\u0600-\u06FF\s'\-]{2,60}$")


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not _NAME_RE.match(v):
            raise ValueError(
                "Name must be 2-60 characters, letters only (no numbers or special chars)."
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if len(v) > 128:
            raise ValueError("Password too long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def no_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("Password required.")
        if len(v) > 128:
            raise ValueError("Password too long.")
        return v


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("At least one uppercase letter required.")
        if not re.search(r"\d", v):
            raise ValueError("At least one digit required.")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: str
    checkin_count: int = 0
    streak: int = 0


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
