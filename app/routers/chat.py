"""
app/routers/chat.py
────────────────────
Endpoints:
  POST /api/chat          — Send a message, get AI response
  GET  /api/chat/history  — Fetch message history
  DELETE /api/chat        — Clear chat history
"""
import random
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status
from bson import ObjectId

from app.core.deps import get_current_user
from app.core.database import get_db
from app.schemas.checkin import ChatMessageCreate, ChatMessageOut

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Simple AI responses (replace with real AI integration)
_AI_RESPONSES = [
    "That sounds really tough. It takes courage to share how you're feeling. 💚",
    "I hear you. You're not alone in this — many people feel that way. Let's breathe through it together.",
    "Thank you for opening up. How long have you been feeling this way?",
    "That makes a lot of sense. Would you like to try a quick breathing exercise?",
    "I'm here for you. Remember — you don't have to carry this alone.",
    "Your feelings are valid. Would you like some coping strategies right now?",
    "It sounds like you're under a lot of pressure. Let's take this one step at a time.",
    "Have you been able to sleep and eat well lately? Sometimes basic self-care can help.",
]


def _fmt(doc: dict) -> ChatMessageOut:
    return ChatMessageOut(
        id=str(doc["_id"]),
        message=doc["message"],
        role=doc["role"],
        created_at=doc["created_at"].isoformat(),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def send_message(
    body: ChatMessageCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> dict:
    """Save user message and return AI response."""
    now = datetime.now(timezone.utc)
    user_id = current_user["_id"]

    # Save user message
    user_msg = {
        "user_id": user_id,
        "message": body.message,
        "role": "user",
        "created_at": now,
    }
    await db.chat_messages.insert_one(user_msg)

    # Generate AI reply
    ai_text = random.choice(_AI_RESPONSES)
    ai_msg = {
        "user_id": user_id,
        "message": ai_text,
        "role": "ai",
        "created_at": now,
    }
    result = await db.chat_messages.insert_one(ai_msg)
    ai_msg["_id"] = result.inserted_id

    return {
        "user_message": body.message,
        "ai_response": _fmt(ai_msg),
    }


@router.get("/history")
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> list[ChatMessageOut]:
    cursor = (
        db.chat_messages.find({"user_id": current_user["_id"]})
        .sort("created_at", -1)
        .limit(limit)
    )
    msgs = [_fmt(doc) async for doc in cursor]
    return list(reversed(msgs))


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    await db.chat_messages.delete_many({"user_id": current_user["_id"]})
