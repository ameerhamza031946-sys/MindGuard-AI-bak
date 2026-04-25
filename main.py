"""
app/main.py
────────────
MindGuard AI — FastAPI Application Entry Point

Security layers:
  ✅ CORS whitelist
  ✅ Security headers middleware (XSS, clickjacking, MIME sniff)
  ✅ Request size limiting
  ✅ Rate limiting via slowapi
  ✅ JWT auth with blacklisting
  ✅ Brute-force lockout
  ✅ Bcrypt password hashing (cost=12)
  ✅ Input validation & sanitization via Pydantic + bleach
  ✅ MongoDB indexes (unique email, TTL for blacklist)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.database import connect_db, close_db, create_indexes
from app.middleware.security import SecurityHeadersMiddleware, LimitRequestSizeMiddleware
from app.routers import auth, checkin, chat

settings = get_settings()

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await create_indexes()
    yield
    await close_db()


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware stack (order matters — last added = first executed) ─────────────

# 1. CORS — must be first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Body size limit (1 MB)
app.add_middleware(LimitRequestSizeMiddleware, max_size=1_048_576)

# 4. Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(checkin.router)
app.include_router(chat.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# ── Global error handler (don't leak stack traces) ────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        raise exc
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )
