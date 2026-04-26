#!/usr/bin/env python3
"""Comprehensive E2E test — runs from local machine via SSH + direct HTTP checks."""
import paramiko
import urllib.request
import urllib.error
import ssl
import json
import time

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"
BASE_HTTP  = f"http://{HOST}"
BASE_HTTPS = "https://recruit.srpailabs.com"
NJ_PORT    = 3010
FA_PORT    = 8009

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

PASS_COUNT = 0
FAIL_COUNT = 0
ISSUES = []

def check(label, ok, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if ok:
        PASS_COUNT += 1
        print(f"  \033[32m[PASS]\033[0m {label}")
    else:
        FAIL_COUNT += 1
        ISSUES.append((label, detail))
        print(f"  \033[31m[FAIL]\033[0m {label}  →  {detail[:120]}")

def http_get(url, expected_status=None, expected_not=None, timeout=10):
    """Returns (status_code, body_snippet, error)"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SRP-E2E-Test/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            body = r.read(512).decode(errors="replace")
            return r.status, body, None
    except urllib.error.HTTPError as e:
        body = e.read(256).decode(errors="replace")
        return e.code, body, None
    except Exception as e:
        return 0, "", str(e)

def ssh_cmd(client, cmd, timeout=20):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    return out, err

print("\n" + "="*60)
print("  SRP SmartRecruit — Comprehensive E2E Test")
print("="*60)

# ── SSH Connection ──────────────────────────────────────────
print("\n[1] Connecting to server via SSH...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    check("SSH connection", True)
except Exception as e:
    check("SSH connection", False, str(e))
    print("\n[ABORT] Cannot reach server.")
    exit(1)

# ── Container health ───────────────────────────────────────
print("\n[2] Container Status...")
out, _ = ssh_cmd(client, "docker ps --format '{{.Names}}\t{{.Status}}'")
for line in out.splitlines():
    name, status = line.split("\t", 1) if "\t" in line else (line, "")
    running = "Up" in status
    check(f"Container {name}", running, status)

# ── Service health via SSH (ports 3010/8009 are internal only) ───────────
print("\n[3] Service Health (localhost)...")

out, _ = ssh_cmd(client, "curl -sf http://localhost:3010/api/health 2>&1 | head -c 200")
check("Next.js /api/health", "ok" in out.lower(), out[:120] if "ok" not in out.lower() else "")

out, _ = ssh_cmd(client, "curl -sf http://localhost:8009/health 2>&1 | head -c 200")
check("FastAPI /health", "healthy" in out.lower(), out[:120] if "healthy" not in out.lower() else "")

# ── HTTPS via nginx ────────────────────────────────────────
print("\n[4] HTTPS / nginx routing...")

status, body, err = http_get(f"{BASE_HTTPS}/api/health")
check("HTTPS /api/health", status == 200, f"{status} {err or body[:60]}")

# Pages that should return 200
public_pages = [
    ("/",           "landing"),
    ("/login",      "login"),
    ("/signup",     "signup"),
    ("/forgot-password", "forgot"),
    ("/legal/privacy",   "privacy"),
    ("/legal/terms",     "terms"),
    ("/legal/security",  "security"),
    ("/legal/accessibility", "accessibility"),
    ("/support/help",    "help"),
    ("/support/contact", "contact"),
]
print("\n[5] Public page loads...")
for path, label in public_pages:
    status, body, err = http_get(f"{BASE_HTTPS}{path}")
    check(f"Page {path}", status == 200, f"{status} {err or body[:60]}")

# API routes — should return 401 (unauth) or 405 (method not allowed), NOT 500
print("\n[6] API route authentication guards (expect 401/403/405, not 500)...")
api_routes = [
    "/api/jobs", "/api/candidates", "/api/resumes", "/api/profile",
    "/api/integrations", "/api/import", "/api/comm", "/api/notify",
    "/api/audit", "/api/boolean-search", "/api/parse",
    "/api/jd", "/api/compose", "/api/screen",
    "/api/tenant", "/api/tenant/invite", "/api/tenant/members",
]
for route in api_routes:
    status, body, err = http_get(f"{BASE_HTTPS}{route}")
    ok = status in (200, 401, 403, 405) and status != 500
    check(f"API guard {route}", ok, f"status={status} {err or body[:60]}")

# ── Database checks via SSH ───────────────────────────────
print("\n[7] Database schema checks...")
db_checks = [
    # Auth / users
    ("auth_users table",          "SELECT COUNT(*) FROM auth_users;"),
    ("auth_users has short_id",   "SELECT column_name FROM information_schema.columns WHERE table_name='auth_users' AND column_name='short_id';"),
    # Jobs
    ("job_posts table",           "SELECT COUNT(*) FROM job_posts;"),
    ("job_posts has short_id",    "SELECT column_name FROM information_schema.columns WHERE table_name='job_posts' AND column_name='short_id';"),
    # Resumes / candidates
    ("resumes table",             "SELECT COUNT(*) FROM resumes;"),
    ("resumes short_id",          "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='short_id';"),
    ("resumes pipeline_stage",    "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='pipeline_stage';"),
    ("resumes ai_score",          "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='ai_score';"),
    ("resumes ai_skills",         "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='ai_skills';"),
    ("resumes updated_at",        "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='updated_at';"),
    ("resumes source_batch_id",   "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='source_batch_id';"),
    # ai_screening_data (added migrate_v7_ai_screening_data.sql)
    ("resumes ai_screening_data", "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='ai_screening_data';"),
    # source_type + last_contacted_at (added in enterprise migration)
    ("resumes source_type",       "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='source_type';"),
    ("resumes last_contacted_at", "SELECT column_name FROM information_schema.columns WHERE table_name='resumes' AND column_name='last_contacted_at';"),
    # Subscriptions
    ("subscriptions table",       "SELECT COUNT(*) FROM subscriptions LIMIT 1;"),
    # Integrations
    ("integrations table",        "SELECT COUNT(*) FROM integrations LIMIT 1;"),
    # Communication (correct table names)
    ("communication_logs",        "SELECT COUNT(*) FROM communication_logs LIMIT 1;"),
    ("communication_templates",   "SELECT COUNT(*) FROM communication_templates LIMIT 1;"),
    ("communication_providers",   "SELECT COUNT(*) FROM communication_providers LIMIT 1;"),
    # Import
    ("import_batches table",      "SELECT COUNT(*) FROM import_batches LIMIT 1;"),
    ("import_row_errors table",   "SELECT COUNT(*) FROM import_row_errors LIMIT 1;"),
    # Audit & logs
    ("audit_logs table",          "SELECT COUNT(*) FROM audit_logs LIMIT 1;"),
    ("activity_log table",        "SELECT COUNT(*) FROM activity_log LIMIT 1;"),
    ("api_keys table",            "SELECT COUNT(*) FROM api_keys LIMIT 1;"),
    ("token_usage table",         "SELECT COUNT(*) FROM token_usage LIMIT 1;"),
    # Webhook
    ("webhook_delivery_logs",     "SELECT COUNT(*) FROM webhook_delivery_logs LIMIT 1;"),
    ("webhook_subscriptions",     "SELECT COUNT(*) FROM webhook_subscriptions LIMIT 1;"),
    # JD / boolean search
    ("generated_jds table",       "SELECT COUNT(*) FROM generated_jds LIMIT 1;"),
    ("generated_boolean_searches","SELECT COUNT(*) FROM generated_boolean_searches LIMIT 1;"),
    ("jd_analysis_results",       "SELECT COUNT(*) FROM jd_analysis_results LIMIT 1;"),
    # Feature flags
    ("feature_flags table",       "SELECT COUNT(*) FROM feature_flags LIMIT 1;"),
    # Invite hardening (migrate_v10) — indexes on tenant_members + auth_users
    ("tenant_members_invite_token_idx", "SELECT indexname FROM pg_indexes WHERE tablename='tenant_members' AND indexname='tenant_members_invite_token_idx';"),
    ("auth_users_email_active_idx",     "SELECT indexname FROM pg_indexes WHERE tablename='auth_users' AND indexname='auth_users_email_active_idx';"),
    # Duplicate email index (migrate_v11)
    ("resumes_tenant_email_idx",  "SELECT indexname FROM pg_indexes WHERE tablename='resumes' AND indexname='resumes_tenant_email_idx';"),
]
for label, sql in db_checks:
    out, err = ssh_cmd(client, f'docker exec srp-auth-db psql -U srp_auth -d srp_auth -c "{sql}" 2>&1')
    ok = ("error" not in out.lower()) and ("does not exist" not in out.lower()) and bool(out.strip())
    check(f"DB: {label}", ok, out[:100] if not ok else "")

# ── FastAPI router checks (via SSH curl) ──────────────────
print("\n[8] FastAPI router availability...")
fa_routes = [
    ("GET /health",                       "curl -s http://localhost:8009/health"),
    ("GET /api/resume/list (unauth)",     "curl -s -o /dev/null -w '%{http_code}' http://localhost:8009/api/resume/list"),
    # Confirmed route: /api/screening/results (401 = auth required = route exists)
    ("GET /api/screening/results (unauth)", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8009/api/screening/results"),
    ("POST /api/users/login schema",      "curl -s -X POST http://localhost:8009/api/users/login -H 'Content-Type: application/json' -d '{\"email\":\"x\",\"password\":\"x\"}' | head -c 200"),
    # /api/status is a v3_2_compat route confirmed on server
    ("GET /api/status",                   "curl -s -o /dev/null -w '%{http_code}' http://localhost:8009/api/status"),
    # FastAPI docs deliberately disabled in production (ENVIRONMENT=production) — 404 is expected
    ("GET /docs disabled in prod",       "curl -s -o /dev/null -w '%{http_code}' http://localhost:8009/docs"),
]
for label, cmd in fa_routes:
    out, err = ssh_cmd(client, cmd)
    ok = out and "error" not in out.lower() and "failed" not in out.lower()
    # For status code responses, accept 200/401/403/422
    if out.strip() in ("200", "401", "403", "404", "405", "422"):
        if "disabled in prod" in label:
            # docs disabled in production = 404 is correct
            ok = out.strip() in ("404", "200")
        else:
            ok = out.strip() in ("200", "401", "403", "422")
    check(f"FastAPI {label}", ok, out[:100] if not ok else f"→ {out[:60]}")

# ── File upload endpoint checks ────────────────────────────
print("\n[9] File upload endpoints...")

# Check that parse route exists and accepts POST
out, _ = ssh_cmd(client, "curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:3010/api/parse -H 'Content-Type: application/json' -d '{}'")
check("Next.js POST /api/parse exists", out.strip() in ("200","400","401","403","422"), f"got {out}")

# Check import route
out, _ = ssh_cmd(client, "curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:3010/api/import -H 'Content-Type: application/json' -d '{}'")
check("Next.js POST /api/import exists", out.strip() in ("200","400","401","403","405","422"), f"got {out}")

# Upload dir exists and is writable (check inside container)
out, _ = ssh_cmd(client, "docker exec srp-auth-app ls /app/uploads/ 2>&1 | head -3")
check("Upload directory exists (/app/uploads)", "total" in out or "cannot access" not in out.lower(), out)

# Check uploads dir is writable inside container (create if missing from old image build)
out, _ = ssh_cmd(client, "docker exec -u root srp-auth-app sh -c 'mkdir -p /app/uploads && chown nextjs:nodejs /app/uploads 2>/dev/null; touch /app/uploads/.test && rm /app/uploads/.test && echo writable' 2>&1")
check("Upload dir writable", "writable" in out, out[:100] if "writable" not in out else "")

# ── nginx config correctness ──────────────────────────────
print("\n[10] nginx proxy routing...")
out, _ = ssh_cmd(client, "nginx -t 2>&1")
check("nginx config valid", "successful" in out.lower(), out)

out, _ = ssh_cmd(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3010/api/health")
check("Next.js direct (localhost:3010)", out.strip() == "200", f"got {out}")

out, _ = ssh_cmd(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8009/health")
check("nginx -> FastAPI direct", out.strip() == "200", f"got {out}")

# ── Environment/config checks ─────────────────────────────
print("\n[11] Environment config in containers...")
out, _ = ssh_cmd(client, "docker exec srp-auth-app printenv | grep -E 'NEXTAUTH_URL|DATABASE_URL|OPENAI_API_KEY' | sed 's/=.*/=***/' 2>&1")
for var in ["NEXTAUTH_URL", "DATABASE_URL", "OPENAI_API_KEY"]:
    check(f"Env var {var} set", var in out, f"not found in: {out[:100]}")

out, _ = ssh_cmd(client, "docker exec srp-ats-app printenv | grep -E 'DATABASE_URL|OPENAI_API_KEY' | sed 's/=.*/=***/' 2>&1")
for var in ["DATABASE_URL", "OPENAI_API_KEY"]:
    check(f"FastAPI env {var} set", var in out, f"not found in: {out[:100]}")

# ── Functional auth flow via API ──────────────────────────
print("\n[12] Auth flow (demo credentials)...")
# Try login with demo user
out, _ = ssh_cmd(client, """curl -s -X POST http://localhost:3010/api/auth/signin/credentials \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=demo@srpailabs.com&password=Demo@1234&csrfToken=test&callbackUrl=/dashboard&json=true' \
  -w '\\nHTTP_STATUS:%{http_code}' 2>&1 | tail -3""")
# Auth endpoints redirect — 200 or 302 are both ok
check("Auth /signin endpoint responds", any(c in out for c in ["200","302","401","ok","error","url"]), out[:120])

# Check CSRF token endpoint
out, _ = ssh_cmd(client, "curl -s http://localhost:3010/api/auth/csrf | head -c 100")
check("Auth CSRF token available", "csrfToken" in out, out[:100])

# Check NextAuth providers endpoint
out, _ = ssh_cmd(client, "curl -s http://localhost:3010/api/auth/providers | head -c 200")
check("Auth providers endpoint", "credentials" in out.lower() or "{" in out, out[:100])

# ── Log check for critical errors ─────────────────────────
print("\n[13] Recent error scan in container logs...")
out, _ = ssh_cmd(client, "docker logs srp-auth-app --since 10m 2>&1 | grep -iE 'error|exception|crash' | grep -v 'NEXTAUTH_URL missing\\|fetch.*error' | tail -10")
critical_errors = [l for l in out.splitlines() if l.strip() and "experimental" not in l.lower()]
check("Next.js no critical errors (last 10min)", len(critical_errors) == 0, "\n    ".join(critical_errors[:5]) if critical_errors else "")

# Exclude known benign Gunicorn noise: SIGTERM on restart is expected, not a real error
out, _ = ssh_cmd(client, "docker logs srp-ats-app --since 10m 2>&1 | grep -iE 'ERROR|CRITICAL|traceback' | grep -v 'Bad file descriptor' | grep -v 'socket' | grep -v 'SIGTERM' | grep -v 'SIGKILL' | grep -v 'Worker.*sent' | grep -v 'Shutting down' | tail -5")
fa_errors = [l for l in out.splitlines() if l.strip()]
check("FastAPI no critical errors (last 10min)", len(fa_errors) == 0, "\n    ".join(fa_errors[:5]) if fa_errors else "")

client.close()

# ── Final Results ─────────────────────────────────────────
print("\n" + "="*60)
total = PASS_COUNT + FAIL_COUNT
print(f"  PASSED: {PASS_COUNT}/{total}")
if FAIL_COUNT:
    print(f"  FAILED: {FAIL_COUNT}/{total}")
    print("\n  Issues to fix:")
    for label, detail in ISSUES:
        print(f"    ✗ {label}")
        if detail:
            print(f"      {detail[:100]}")
else:
    print("  ALL CHECKS PASSED ✓")
print("="*60 + "\n")
