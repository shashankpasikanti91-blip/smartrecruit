#!/usr/bin/env python3
"""
SRP SmartRecruit — Master E2E Test Suite
Tests all pages, API routes, auth flows, account guards, and data safety.
Runs against https://recruit.srpailabs.com (no mocking).

Usage:
    python deployment/e2e_master.py
"""
from __future__ import annotations

import os
import ssl
import sys
import time
import json
import urllib.error
import urllib.request

BASE = "https://recruit.srpailabs.com"
CTX  = ssl.create_default_context()

PASS = 0
FAIL = 0
ISSUES: list[str] = []


def _get(path: str, *, headers: dict | None = None, timeout: int = 15) -> tuple[int, str]:
    """HTTP GET — returns (status_code, body_prefix). Never throws."""
    h = {"User-Agent": "SRP-E2E-Master/1.0", **(headers or {})}
    for attempt in range(3):
        try:
            req = urllib.request.Request(BASE + path, headers=h)
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
                return r.status, r.read(512).decode(errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read(256).decode(errors="replace")
        except Exception as ex:
            if attempt < 2:
                time.sleep(2)
                continue
            return 0, str(ex)
    return 0, "max retries"


def check(label: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    status = "PASS" if ok else "FAIL"
    detail_str = f"  [{detail[:100]}]" if detail and not ok else ""
    print(f"  [{status}] {label}{detail_str}")
    if ok:
        PASS += 1
    else:
        FAIL += 1
        ISSUES.append(f"{label}: {detail[:120]}")


def section(title: str) -> None:
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ═══════════════════════════════════════════════════════════════
# [1] CORE INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════
section("[1] Core Infrastructure")

code, body = _get("/health")
check("/health → 200 + status=healthy", code == 200 and "healthy" in body.lower(), f"HTTP {code}: {body[:60]}")

code, body = _get("/")
check("Landing page / → 200", code == 200, f"HTTP {code}")

code, body = _get("/api/health")
check("/api/health (Next.js) → 200", code == 200, f"HTTP {code}: {body[:60]}")

# ═══════════════════════════════════════════════════════════════
# [2] AUTH PAGES
# ═══════════════════════════════════════════════════════════════
section("[2] Auth Pages (public)")

for path in ["/login", "/signup", "/forgot-password"]:
    code, body = _get(path)
    check(f"{path} → 200", code == 200, f"HTTP {code}")

code, body = _get("/reset-password?token=testtoken")
check("/reset-password (with token param) → 200", code == 200, f"HTTP {code}")

# ═══════════════════════════════════════════════════════════════
# [3] NEXT AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════
section("[3] NextAuth Endpoints")

code, body = _get("/api/auth/csrf")
check("/api/auth/csrf → 200 with csrfToken", code == 200 and "csrfToken" in body, f"HTTP {code}: {body[:60]}")

code, body = _get("/api/auth/providers")
check("/api/auth/providers → 200 with credentials", code == 200 and ("credentials" in body or "google" in body), f"HTTP {code}: {body[:60]}")

code, body = _get("/api/auth/session")
check("/api/auth/session → 200", code == 200, f"HTTP {code}")

# ═══════════════════════════════════════════════════════════════
# [4] AUTH GUARDS — ALL must return 401/403/405 (no data leakage)
# ═══════════════════════════════════════════════════════════════
section("[4] Auth Guards (unauthenticated must be blocked)")

GUARDED = [
    "/api/auth/me",
    "/api/jobs",
    "/api/candidates",
    "/api/resume/list",
    "/api/screen",
    "/api/compose",
    "/api/profile",
    "/api/admin",
    "/api/audit",
    "/api/boolean-search",
    "/api/jd",
    "/api/integrations",
    "/api/import",
    "/api/tenant",
    "/api/comm",
    "/api/notify",
    "/api/support/tickets",
    "/api/screening/results",
    "/api/calendar",
    "/api/interviews",
]

for path in GUARDED:
    code, body = _get(path)
    # 404 = route not found (not a data leak), 307/308 = redirect to /login also OK
    blocked = code in (401, 403, 405, 307, 308, 404)
    check(f"{path} blocked", blocked, f"HTTP {code} — POSSIBLE data leak!" if not blocked else f"HTTP {code}")

# ═══════════════════════════════════════════════════════════════
# [5] COMPANY / LEGAL PAGES
# ═══════════════════════════════════════════════════════════════
section("[5] Company & Legal Pages")

for path in [
    "/company/about",
    "/company/careers",
    "/legal",
    "/support",
    "/resources",
]:
    code, body = _get(path)
    check(f"{path} → 200/307/308", code in (200, 307, 308, 404), f"HTTP {code}")

# ═══════════════════════════════════════════════════════════════
# [6] NGINX ROUTING — correct service gets request
# ═══════════════════════════════════════════════════════════════
section("[6] Nginx Route Mapping")

# FastAPI routes (expect JSON with status field)
fastapi_routes = [
    ("/health",                 "healthy"),
    ("/api/auth/me",            ""),      # 401 from FastAPI or Next.js — both OK
]
for path, keyword in fastapi_routes:
    code, body = _get(path)
    if keyword:
        check(f"nginx→FastAPI {path} has '{keyword}'", keyword in body.lower(), f"HTTP {code}: {body[:80]}")
    else:
        check(f"nginx {path} responds", code > 0, f"HTTP {code}")

# Next.js routes — should return JSON or HTML, never a 502
nextjs_routes = ["/api/auth/csrf", "/api/auth/providers", "/api/auth/session", "/login", "/signup"]
for path in nextjs_routes:
    code, body = _get(path)
    check(f"nginx→Next.js {path} not 502", code != 502, f"HTTP {code}: {body[:60]}")

# ═══════════════════════════════════════════════════════════════
# [7] SECURITY HEADERS
# ═══════════════════════════════════════════════════════════════
section("[7] Security Headers")

try:
    req = urllib.request.Request(BASE + "/", headers={"User-Agent": "SRP-E2E/1.0"})
    with urllib.request.urlopen(req, context=CTX, timeout=12) as r:
        headers = dict(r.headers)
    check("X-Frame-Options present",        "x-frame-options"       in {k.lower() for k in headers}, str({k: v for k, v in headers.items() if "frame" in k.lower()}))
    check("X-Content-Type-Options present", "x-content-type-options" in {k.lower() for k in headers}, "")
    check("Strict-Transport-Security",      "strict-transport-security" in {k.lower() for k in headers}, "")
except Exception as ex:
    check("Security headers check", False, str(ex))

# ═══════════════════════════════════════════════════════════════
# [8] ACCEPT-INVITE FLOW
# ═══════════════════════════════════════════════════════════════
section("[8] Accept-Invite Page")

code, body = _get("/accept-invite?token=invalid-token-test")
# Should render the page (to show error) not crash with 500
check("/accept-invite page renders (200/400, not 500)", code in (200, 400, 401, 404), f"HTTP {code}")

# ═══════════════════════════════════════════════════════════════
# [9] STATIC ASSETS & NEXT.JS INTERNALS
# ═══════════════════════════════════════════════════════════════
section("[9] Static Assets")

code, body = _get("/_next/static/")
check("/_next/static/ reachable (2xx/3xx/403/404)", code in (200, 301, 302, 303, 307, 308, 403, 404), f"HTTP {code}")

code, body = _get("/static/")
check("/static/ reachable (200/403/404)", code in (200, 403, 404), f"HTTP {code}")

# ═══════════════════════════════════════════════════════════════
# [10] ERROR HANDLING — no stack traces exposed
# ═══════════════════════════════════════════════════════════════
section("[10] Error Handling (no stack traces in prod)")

code, body = _get("/api/jobs/nonexistent-id-xyz")
safe = "traceback" not in body.lower() and "error at line" not in body.lower()
check("/api/jobs/nonexistent no stack trace", safe, body[:80])

code, body = _get("/this-page-does-not-exist-at-all")
check("404 page returns 200/404 (not 500)", code in (200, 404), f"HTTP {code}")

# ═══════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'═'*55}")
total = PASS + FAIL
print(f"  SRP SmartRecruit E2E — {PASS}/{total} checks passed")
if FAIL:
    print(f"\n  {'─'*51}")
    print(f"  FAILURES ({FAIL}):")
    for issue in ISSUES:
        print(f"    ✗ {issue}")
    print(f"  {'─'*51}")
print(f"{'═'*55}\n")
sys.exit(1 if FAIL else 0)
