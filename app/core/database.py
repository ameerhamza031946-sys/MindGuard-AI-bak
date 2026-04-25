"""
app/core/database.py
─────────────────────
Async MongoDB connection via Motor.
Provides a single shared client and db handle.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings

settings = get_settings()

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    global _client
    _client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=10,
        minPoolSize=0,
    )
    try:
        # Verify connection (max 5s)
        await _client.admin.command("ping")
        print(f"[OK] MongoDB connected -> {settings.DATABASE_NAME}")
    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        # Note: We don't raise here so the app can still boot, 
        # allowing you to see logs or use parts of the app that don't need DB.


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        print("[INFO] MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("Database not initialised. Call connect_db() first.")
    return _client[settings.DATABASE_NAME]


async def create_indexes() -> None:
    """Create all necessary MongoDB indexes for performance & uniqueness."""
    try:
        db = get_db()

        # Users
        await db.users.create_index("email", unique=True)
        await db.users.create_index("created_at")

        # Token blacklist (auto-expire via TTL)
        await db.token_blacklist.create_index(
            "expires_at", expireAfterSeconds=0
        )

        # Checkins
        await db.checkins.create_index([("user_id", 1), ("created_at", -1)])

        # Chat messages
        await db.chat_messages.create_index([("user_id", 1), ("created_at", -1)])

        # Rate limit / login attempts
        await db.login_attempts.create_index(
            "expires_at", expireAfterSeconds=0
        )
        await db.login_attempts.create_index("email")

        print("[OK] MongoDB indexes created")
    except Exception as e:
        print(f"[WARNING] Could not create MongoDB indexes: {e}")
