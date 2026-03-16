"""
Database Connection Configuration
PostgreSQL only — no SQLite fallback.
Set DATABASE_URL in your .env file.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL is required — no SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set.\n"
        "Set it in your .env file, e.g.:\n"
        "  DATABASE_URL=postgresql://srp_ats:password@localhost:5434/srp_ats\n"
        "Run 'docker compose -f docker-compose.dev.yml up db -d' to start a local PostgreSQL."
    )

# Normalise: Supabase/Heroku-style postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL.startswith("postgresql"):
    raise RuntimeError(
        f"DATABASE_URL must be a PostgreSQL URL (got: {DATABASE_URL[:30]}...)\n"
        "SQLite is not supported. Use PostgreSQL."
    )

# Disable SQL echo in production
_SQL_ECHO = os.getenv("ENVIRONMENT", "development").lower() not in ("production", "prod")

engine = create_engine(
    DATABASE_URL,
    echo=_SQL_ECHO,
    pool_pre_ping=True,   # detect stale connections
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,    # recycle connections every 30 min
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database session
    Usage in FastAPI: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    # Import all models here to register them with Base
    from app.models import user, resume, screening, support
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_all_tables():
    """Drop all tables - USE WITH CAUTION"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped")
