"""
app/schemas/checkin.py & chat
"""
from pydantic import BaseModel, field_validator
from typing import Optional
import bleach


class CheckinCreate(BaseModel):
    stress_level: int
    note: Optional[str] = None

    @field_validator("stress_level")
    @classmethod
    def valid_range(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("Stress level must be 0-100.")
        return v

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = bleach.clean(v.strip(), tags=[], strip=True)
        if len(v) > 500:
            raise ValueError("Note must be under 500 characters.")
        return v or None


class CheckinOut(BaseModel):
    id: str
    stress_level: int
    note: Optional[str]
    label: str          # LOW / MODERATE / HIGH
    created_at: str


class ChatMessageCreate(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def sanitize(cls, v: str) -> str:
        v = bleach.clean(v.strip(), tags=[], strip=True)
        if not v:
            raise ValueError("Message cannot be empty.")
        if len(v) > 1000:
            raise ValueError("Message too long (max 1000 chars).")
        return v


class ChatMessageOut(BaseModel):
    id: str
    message: str
    role: str           # "user" or "ai"
    created_at: str
