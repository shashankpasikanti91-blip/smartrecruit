"""
SRP SmartRecruit v3.2
Main FastAPI Application Entry Point
High-Security ATS with AI Capabilities
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
import os
import time
from pathlib import Path

# Import database
from app.database.connection import engine, Base, init_db

#Import routers
from app.routers import auth, screening, resume, support, ai_assistant, v3_2_compat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting SRP SmartRecruit v3.2...")
    init_db()
    logger.info("✅ Database initialized")
    
    # Seed demo user if it doesn't exist
    try:
        from app.database.connection import SessionLocal
        from app.models.user import User
        from app.auth.utils import hash_password
        db = SessionLocal()
        demo = db.query(User).filter(User.email == "demo@srp.com").first()
        if not demo:
            demo = User(
                email="demo@srp.com",
                hashed_password=hash_password("Demo@1234"),
                role="user",
                is_active=True,
                is_verified=True
            )
            db.add(demo)
            db.commit()
            logger.info("✅ Demo user created (demo@srp.com / Demo@1234)")
        else:
            logger.info("✅ Demo user already exists")
        db.close()
    except Exception as e:
        logger.warning(f"⚠️ Could not seed demo user: {e}")
    
    yield
    # Shutdown
    logger.info("👋 Shutting down SRP SmartRecruit v3.2")


# Initialize FastAPI app
_env = os.getenv("ENVIRONMENT", "development").lower()
_is_prod = _env in ("production", "prod")

app = FastAPI(
    title="SRP SmartRecruit v3.2",
    description="High-Security AI-Powered Applicant Tracking System",
    version="3.2.0",
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
    lifespan=lifespan
)

# ── Security headers middleware ──────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Response-Time"] = f"{time.monotonic() - start:.4f}s"
        response.headers.pop("server", None)
        if _is_prod:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── Trusted host guard (prod only) ───────────────────────────────────────────
_allowed_hosts_raw = os.getenv("ALLOWED_HOSTS", "")
if _is_prod and _allowed_hosts_raw:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[h.strip() for h in _allowed_hosts_raw.split(",") if h.strip()]
    )

# CORS Middleware
# In production, restrict to your actual domain(s) via CORS_ORIGINS env var
_cors_origins_raw = os.getenv("CORS_ORIGINS", "")
if _cors_origins_raw:
    _cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
elif _is_prod:
    _cors_origins = []
    logger.warning("CORS_ORIGINS not set in production! All cross-origin requests will be blocked.")
else:
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ── Global exception handlers — never leak stack traces ──────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred. Please try again."})

# Create necessary directories
# backend/app/main.py → parent = backend/app/, parent.parent = backend/ (or /app/ in Docker)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent

# Templates/static: local dev has frontend/ sibling; Docker has flat layout at WORKDIR
_FRONTEND_DIR = _PROJECT_ROOT / "frontend"
if _FRONTEND_DIR.is_dir():
    TEMPLATES_DIR = _FRONTEND_DIR / "templates"
    STATIC_DIR    = _FRONTEND_DIR / "static"
else:
    TEMPLATES_DIR = _BACKEND_DIR / "templates"
    STATIC_DIR    = _BACKEND_DIR / "static"

# Uploads: project root / uploads (local) or /app/uploads (Docker)
UPLOADS_DIR = _PROJECT_ROOT / "uploads" if _PROJECT_ROOT != Path("/") else _BACKEND_DIR / "uploads"

# Create directories if they don't exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Setup templates and static files
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
if UPLOADS_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


# Root endpoint — serve landing page
@app.get("/")
async def root(request: Request):
    """Landing / marketing page"""
    return templates.TemplateResponse(
        "landing.html",
        {"request": request, "version": "3.2.0"}
    )


@app.get("/health")
async def health_check():
    """Detailed health check — pings the database"""
    from app.database.connection import SessionLocal
    import sqlalchemy
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(sqlalchemy.text("SELECT 1"))
        db_ok = True
        db.close()
    except Exception:
        pass
    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "3.2.0",
        "environment": _env,
        "database": "connected" if db_ok else "unreachable",
    }


# Main UI endpoint — serve the v3.2 dashboard app
@app.get("/app")
async def serve_app(request: Request):
    """Serve the main application UI"""
    return templates.TemplateResponse(
        "dashboard_v3_2.html",
        {"request": request, "version": "3.2.0"}
    )

# Legacy redirect: /dashboard → /app
@app.get("/dashboard")
async def dashboard_redirect():
    return RedirectResponse(url="/app", status_code=301)


# Include routers
app.include_router(v3_2_compat.router)  # v3.2 compatibility endpoints FIRST
app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(screening.router)
app.include_router(ai_assistant.router)
app.include_router(support.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
