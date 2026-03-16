"""
setup_local_db.py — One-time local PostgreSQL setup for SRP SmartRecruit ATS
Connects as postgres superuser and creates:
  - User:     srp_ats  (with the password in your .env)
  - Database: srp_ats  (owned by srp_ats)

Usage:
    python setup_local_db.py
    # Enter your postgres superuser password when prompted
"""

import os
import sys
import getpass
from pathlib import Path

# ── Load .env to get the target credentials ───────────────────────────────
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "")
if not DB_URL or not DB_URL.startswith("postgresql://"):
    print("ERROR: DATABASE_URL not set or not a PostgreSQL URL in .env")
    sys.exit(1)

# Parse DATABASE_URL: postgresql://user:password@host:port/dbname
from urllib.parse import urlparse
parsed = urlparse(DB_URL)
ATS_USER     = parsed.username        # srp_ats
ATS_PASSWORD = parsed.password        # ats_dev_password
ATS_HOST     = parsed.hostname        # localhost
ATS_PORT     = parsed.port or 5432
ATS_DB       = parsed.path.lstrip("/")  # srp_ats

print(f"Will create user '{ATS_USER}' and database '{ATS_DB}' on {ATS_HOST}:{ATS_PORT}")
print()

# ── Get postgres superuser password ───────────────────────────────────────
# Priority: PG_ADMIN_PASSWORD env var > command-line arg > interactive prompt
pg_password = (
    os.getenv("PG_ADMIN_PASSWORD")
    or (sys.argv[1] if len(sys.argv) > 1 else None)
    or getpass.getpass("Enter your local PostgreSQL superuser (postgres) password: ")
)

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# ── Connect as postgres superuser (to 'postgres' maintenance DB) ─────────
try:
    conn = psycopg2.connect(
        host=ATS_HOST,
        port=ATS_PORT,
        dbname="postgres",
        user="postgres",
        password=pg_password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    print("✅ Connected to local PostgreSQL as superuser")
except Exception as e:
    print(f"❌ Could not connect: {e}")
    sys.exit(1)

# ── Create user if not exists ─────────────────────────────────────────────
cur.execute("SELECT 1 FROM pg_user WHERE usename = %s", (ATS_USER,))
if cur.fetchone():
    print(f"   User '{ATS_USER}' already exists — updating password")
    cur.execute(f"ALTER USER {ATS_USER} WITH PASSWORD %s;", (ATS_PASSWORD,))
else:
    cur.execute(
        f"CREATE USER {ATS_USER} WITH PASSWORD %s CREATEDB;",
        (ATS_PASSWORD,)
    )
    print(f"✅ Created user '{ATS_USER}'")

# ── Create database if not exists ─────────────────────────────────────────
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (ATS_DB,))
if cur.fetchone():
    print(f"   Database '{ATS_DB}' already exists — skipping creation")
else:
    cur.execute(
        f"CREATE DATABASE {ATS_DB} OWNER {ATS_USER} ENCODING 'UTF8' "
        f"LC_COLLATE 'en-US' LC_CTYPE 'en-US' TEMPLATE template0;"
    )
    print(f"✅ Created database '{ATS_DB}' owned by '{ATS_USER}'")

# ── Grant privileges ──────────────────────────────────────────────────────
cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {ATS_DB} TO {ATS_USER};")
print(f"✅ Granted all privileges on '{ATS_DB}' to '{ATS_USER}'")

cur.close()
conn.close()

# ── Initialize app tables (SQLAlchemy) ────────────────────────────────────
print()
print("Creating application tables via SQLAlchemy...")
try:
    from app.database.connection import init_db
    init_db()
    print("✅ All tables created successfully")
except Exception as e:
    print(f"❌ Table creation failed: {e}")
    print("   Try running the app once — tables are created on startup.")
    sys.exit(1)

print()
print("=" * 55)
print("✅ Local PostgreSQL setup complete!")
print(f"   Host:     {ATS_HOST}:{ATS_PORT}")
print(f"   Database: {ATS_DB}")
print(f"   User:     {ATS_USER}")
print()
print("You can now start the app:")
print("  .venv\\Scripts\\uvicorn.exe app.main:app --port 8767 --reload")
print("=" * 55)
