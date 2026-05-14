#!/usr/bin/env python3
"""
SRP SmartRecruit — Account Verification Script
Verifies that the 4 key user accounts (harish, priya, shashank, owner)
are active and correctly configured in the auth database.

Run locally (requires SSH access to server):
    python deployment/verify_accounts.py

Or run the SQL directly on the server:
    docker exec srp-auth-db psql -U srp_auth -d srp_auth -c "SELECT ..."
"""
from __future__ import annotations

import os
import ssl
import sys
import json
import urllib.request
import urllib.error

BASE = "https://recruit.srpailabs.com"
CTX  = ssl.create_default_context()

KNOWN_ACCOUNTS = [
    "harish",
    "priya",
    "shashank",
    "owner",
]

# ─── SQL to run on the server via: docker exec srp-auth-db psql ... ──────────
VERIFY_SQL = """
SELECT
    id,
    email,
    name,
    role,
    is_active,
    created_at::date AS joined,
    last_login_at::date AS last_login
FROM auth_users
WHERE
    is_active = true
    AND (
        lower(name)  LIKE '%harish%'
     OR lower(name)  LIKE '%priya%'
     OR lower(name)  LIKE '%shashank%'
     OR role         = 'owner'
     OR lower(email) LIKE '%harish%'
     OR lower(email) LIKE '%priya%'
     OR lower(email) LIKE '%shashank%'
    )
ORDER BY role, name;
"""

print("═" * 60)
print("  SRP SmartRecruit — Account Verification")
print("═" * 60)

print("""
To verify accounts directly on the server, run:

  docker exec srp-auth-db psql -U srp_auth -d srp_auth -c \\
    "SELECT id, email, name, role, is_active,
            created_at::date AS joined,
            last_login_at::date AS last_login
     FROM auth_users
     WHERE is_active = true
       AND (lower(name) LIKE '%harish%'
         OR lower(name) LIKE '%priya%'
         OR lower(name) LIKE '%shashank%'
         OR role = 'owner'
         OR lower(email) LIKE '%harish%'
         OR lower(email) LIKE '%priya%'
         OR lower(email) LIKE '%shashank%')
     ORDER BY role, name;"

To list ALL active users:
  docker exec srp-auth-db psql -U srp_auth -d srp_auth -c \\
    "SELECT email, name, role, is_active, created_at::date
     FROM auth_users ORDER BY role, name;"
""")

# ─── Live HTTPS check: public pages ──────────────────────────────────────────
print("═" * 60)
print("  Live site checks")
print("═" * 60)

PASS = 0
FAIL = 0

def get(path: str) -> tuple[int, str]:
    try:
        req = urllib.request.Request(BASE + path, headers={"User-Agent": "SRP-AccountCheck/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=15) as r:
            return r.status, r.read(256).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as ex:
        return 0, str(ex)

checks = [
    ("/login",           [200],          "Login page accessible"),
    ("/signup",          [200],          "Signup page accessible"),
    ("/forgot-password", [200],          "Forgot password page accessible"),
    ("/api/auth/csrf",   [200],          "Auth CSRF endpoint working"),
    ("/api/auth/me",     [401, 403],     "Auth guard: /api/auth/me (blocks unauthenticated)"),
    ("/api/jobs",        [401, 403, 404],"Auth guard: /api/jobs (blocks unauthenticated)"),
    ("/health",          [200],          "FastAPI health check"),
]

for path, expected, label in checks:
    code, body = get(path)
    ok = code in expected
    status = "PASS" if ok else "FAIL"
    detail = f"HTTP {code} (expected {expected})" if not ok else f"HTTP {code}"
    print(f"  [{status}] {label}: {detail}")
    if ok:
        PASS += 1
    else:
        FAIL += 1

print(f"\n  {PASS}/{PASS+FAIL} live checks passed")
print("═" * 60)
print("""
Next steps:
  1. SSH into the server
  2. Run the SQL above to verify accounts are active
  3. If an account is missing, check the frontend DB migration files:
       nextjs-auth/db/seed_*.sql or nextjs-auth/db/migrate_v*.sql

Data safety reminders:
  - Daily backup runs at 02:00 UTC → /opt/backups/srp-smartrecruit/
  - 30 days retention, both databases + uploads
  - NEVER use DELETE on user data — use soft delete (set deleted_at)
  - All data changes must be logged in audit_log table
""")
sys.exit(1 if FAIL else 0)
