"""
app/routers/checkin.py
───────────────────────
Endpoints:
  POST /api/checkins          — Log a new stress check-in
  GET  /api/checkins          — Get user's check-in history
  GET  /api/checkins/trends   — Weekly stress trend data
  GET  /api/checkins/stats    — Aggregate stats (avg, streak, etc.)
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId

from app.core.deps import get_current_user
from app.core.database import get_db
from app.schemas.checkin import CheckinCreate, CheckinOut

router = APIRouter(prefix="/api/checkins", tags=["checkins"])


def _stress_label(val: int) -> str:
    if val < 33:
        return "LOW"
    elif val < 66:
        return "MODERATE"
    return "HIGH"


def _fmt(doc: dict) -> CheckinOut:
    return CheckinOut(
        id=str(doc["_id"]),
        stress_level=doc["stress_level"],
        note=doc.get("note"),
        label=_stress_label(doc["stress_level"]),
        created_at=doc["created_at"].isoformat(),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_checkin(
    body: CheckinCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> CheckinOut:
    """Log a new stress check-in and update streak."""
    now = datetime.now(timezone.utc)
    user_id = current_user["_id"]

    doc = {
        "user_id": user_id,
        "stress_level": body.stress_level,
        "note": body.note,
        "label": _stress_label(body.stress_level),
        "created_at": now,
    }
    result = await db.checkins.insert_one(doc)
    doc["_id"] = result.inserted_id

    # Update streak & checkin_count on user
    last_date = current_user.get("last_checkin_date")
    today = now.date()
    streak = current_user.get("streak", 0)

    if last_date:
        last = last_date.date() if hasattr(last_date, 'date') else last_date
        if last == today - timedelta(days=1):
            streak += 1
        elif last < today - timedelta(days=1):
            streak = 1
        # same day → don't increment
    else:
        streak = 1

    await db.users.update_one(
        {"_id": user_id},
        {
            "$inc": {"checkin_count": 1},
            "$set": {"streak": streak, "last_checkin_date": now},
        },
    )

    return _fmt(doc)


@router.get("")
async def get_checkins(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> list[CheckinOut]:
    """Get paginated check-in history."""
    cursor = (
        db.checkins.find({"user_id": current_user["_id"]})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [_fmt(doc) async for doc in cursor]


@router.get("/trends")
async def get_trends(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> dict:
    """Return last 7 days of average stress per day."""
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    pipeline = [
        {
            "$match": {
                "user_id": current_user["_id"],
                "created_at": {"$gte": seven_days_ago},
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "avg_stress": {"$avg": "$stress_level"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    results = []
    async for doc in db.checkins.aggregate(pipeline):
        results.append(
            {
                "date": doc["_id"],
                "avg_stress": round(doc["avg_stress"], 1),
                "count": doc["count"],
                "label": _stress_label(int(doc["avg_stress"])),
            }
        )

    return {"trends": results}


@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> dict:
    """Aggregate stats: overall average, highest, lowest stress."""
    pipeline = [
        {"$match": {"user_id": current_user["_id"]}},
        {
            "$group": {
                "_id": None,
                "avg_stress": {"$avg": "$stress_level"},
                "max_stress": {"$max": "$stress_level"},
                "min_stress": {"$min": "$stress_level"},
                "total": {"$sum": 1},
            }
        },
    ]
    result = None
    async for doc in db.checkins.aggregate(pipeline):
        result = doc

    if not result:
        return {
            "avg_stress": 0,
            "max_stress": 0,
            "min_stress": 0,
            "total_checkins": 0,
            "streak": current_user.get("streak", 0),
        }

    return {
        "avg_stress": round(result["avg_stress"], 1),
        "max_stress": result["max_stress"],
        "min_stress": result["min_stress"],
        "total_checkins": result["total"],
        "streak": current_user.get("streak", 0),
    }
