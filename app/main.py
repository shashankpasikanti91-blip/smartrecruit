"""
SRP SmartRecruit v3.2
Main FastAPI Application Entry Point
High-Security ATS with AI Capabilities
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
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
    yield
    # Shutdown
    logger.info("👋 Shutting down SRP SmartRecruit v3.2")


# Initialize FastAPI app
app = FastAPI(
    title="SRP SmartRecruit v3.2",
    description="High-Security AI-Powered Applicant Tracking System",
    version="3.2.0",
    lifespan=lifespan
)

# CORS Middleware
# In production, restrict to your actual domain(s) via CORS_ORIGINS env var
_env = os.getenv("ENVIRONMENT", "development").lower()
_cors_origins_raw = os.getenv("CORS_ORIGINS", "")
if _cors_origins_raw:
    _cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
elif _env in ("production", "prod"):
    # Deny wildcard in production — must set CORS_ORIGINS
    _cors_origins = []
    logger.warning("CORS_ORIGINS not set in production! All cross-origin requests will be blocked.")
else:
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"

# Create directories if they don't exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

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
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "3.2.0",
        "database": "connected"
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
    from fastapi.responses import RedirectResponse
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
        host="0.0.0.0",
        port=5003,
        reload=True,
        log_level="info"
    )
