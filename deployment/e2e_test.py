#!/usr/bin/env python3
"""Remote end-to-end checks — covers FastAPI ATS + Next.js auth frontend."""

from __future__ import annotations

import ssl
import sys
import urllib.error
import urllib.request

from remote_config import load_remote_config, open_ssh_client


CTX = ssl.create_default_context()
PASS_COUNT = 0
FAIL_COUNT = 0
ISSUES: list[tuple[str, str]] = []


def http_get(url: str, timeout: int = 10) -> tuple[int, str, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SRP-E2E-Test/2.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as response:
            return response.status, response.read(512).decode(errors="replace"), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(256).decode(errors="replace"), None
    except Exception as exc:
        return 0, "", str(exc)


def ssh_cmd(client, command: str, timeout: int = 30) -> tuple[str, str]:
    _, stdout, stderr = client.exec_command(command, timeout=timeout)
    return (
        stdout.read().decode(errors="replace").strip(),
        stderr.read().decode(errors="replace").strip(),
    )


def check(label: str, ok: bool, detail: str = "") -> bool:
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if ok else "FAIL"
    suffix = f" -> {detail[:140]}" if detail else ""
    print(f"  [{status}] {label}{suffix}")
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
        ISSUES.append((label, detail))
    return ok


def main() -> None:
    config = load_remote_config(require_domain=True)
    client = open_ssh_client(config)

    try:
        print("\n" + "=" * 60)
        print("  SRP SmartRecruit — Full-Stack Remote E2E Test")
        print("=" * 60)

        # ── [1] HTTPS health and landing page ──────────────────────────
        print("\n[1] HTTPS health and landing page")
        status, body, err = http_get(f"{config.base_https}/health")
        check("HTTPS /health → 200", status == 200, f"{status} {err or body[:80]}")

        status, body, err = http_get(f"{config.base_https}/")
        check("HTTPS / → 200", status == 200, f"{status} {err or body[:80]}")

        # ── [2] FastAPI guarded routes ──────────────────────────────────
        print("\n[2] FastAPI auth guards (must return 401/403/405)")
        for route in [
            "/api/auth/me",
            "/api/resume/list",
            "/api/support/tickets",
            "/api/screening/results",
        ]:
            status, body, err = http_get(f"{config.base_https}{route}")
            check(route, status in (401, 403, 405), f"{status} {err or body[:80]}")

        # ── [3] FastAPI localhost health ────────────────────────────────
        print(f"\n[3] FastAPI container (localhost:{config.app_port})")
        out, err = ssh_cmd(client, f"curl -sf http://127.0.0.1:{config.app_port}/health")
        check("FastAPI /health healthy", "healthy" in out.lower(), err or out[:120])

        # ── [4] Next.js localhost health ────────────────────────────────
        print("\n[4] Next.js auth container (localhost:3010)")
        out, err = ssh_cmd(client, "curl -sf http://127.0.0.1:3010/api/health")
        check("Next.js /api/health → 200", out.strip() != "" and "error" not in out.lower(), err or out[:120])

        # ── [5] NextAuth endpoints ──────────────────────────────────────
        print("\n[5] NextAuth endpoints")
        out, err = ssh_cmd(client, "curl -s http://127.0.0.1:3010/api/auth/csrf")
        check("CSRF token available", "csrfToken" in out, err or out[:100])

        out, err = ssh_cmd(client, "curl -s http://127.0.0.1:3010/api/auth/providers")
        check("Auth providers endpoint", "credentials" in out.lower() or ("{" in out and "}" in out), err or out[:100])

        # ── [6] HTTPS NextAuth via nginx proxy ──────────────────────────
        print("\n[6] NextAuth via HTTPS/nginx routing")
        status, body, err = http_get(f"{config.base_https}/api/auth/csrf")
        check("HTTPS /api/auth/csrf → 200", status == 200, f"{status} {err or body[:80]}")

        status, body, err = http_get(f"{config.base_https}/api/auth/providers")
        check("HTTPS /api/auth/providers → 200", status == 200, f"{status} {err or body[:80]}")

        # ── [7] Next.js pages via HTTPS ─────────────────────────────────
        print("\n[7] Next.js page routes via HTTPS")
        for page in ["/login", "/signup"]:
            status, body, err = http_get(f"{config.base_https}{page}")
            check(f"HTTPS {page} → 200/307", status in (200, 307, 308), f"{status} {err or body[:60]}")

        # ── [8] Container status ─────────────────────────────────────────
        print("\n[8] Docker container status")
        out, err = ssh_cmd(client, "docker ps --format '{{.Names}} {{.Status}}'")
        check("srp-ats-app running", "srp-ats-app" in out and "Up" in out, err or out[:200])
        check("srp-auth-app running", "srp-auth-app" in out and "Up" in out, err or out[:200])
        check("srp-ats-db running", "srp-ats-db" in out and "Up" in out, err or out[:200])
        check("srp-auth-db running", "srp-auth-db" in out and "Up" in out, err or out[:200])

        # ── [9] Nginx ───────────────────────────────────────────────────
        print("\n[9] Nginx configuration")
        out, err = ssh_cmd(client, "nginx -t 2>&1")
        check("nginx config valid", "successful" in (out + err).lower(), (out + err)[:120])

        # ── [10] Network isolation ──────────────────────────────────────
        print("\n[10] Network isolation (other projects not disrupted)")
        out, err = ssh_cmd(client, "docker network ls --format '{{.Name}}'")
        check("srp_ats_internal network exists", "srp_ats_internal" in out, err or out[:200])
        check("srp_auth_net network exists", "srp_auth_net" in out, err or out[:200])

        # ── [11] Volume integrity ────────────────────────────────────────
        print("\n[11] Volume integrity")
        out, err = ssh_cmd(client, "docker volume ls --format '{{.Name}}'")
        check("ats_postgres_data volume present", "ats_postgres_data" in out, err or out[:200])
        check("srp_auth_pgdata volume present", "srp_auth_pgdata" in out, err or out[:200])

        # ── [12] Recent log error scan ───────────────────────────────────
        print("\n[12] Recent log error scan (last 10 min)")
        out, err = ssh_cmd(
            client,
            "docker logs srp-auth-app --since 10m 2>&1 "
            "| grep -iE 'error|exception|crash' "
            "| grep -vE 'NEXTAUTH_URL missing|fetch.*error|ExperimentalWarning' "
            "| tail -10",
        )
        critical = [ln for ln in out.splitlines() if ln.strip() and "experimental" not in ln.lower()]
        check("Next.js no critical errors (10m)", len(critical) == 0, "\n    ".join(critical[:5]))

        out, err = ssh_cmd(
            client,
            "docker logs srp-ats-app --since 10m 2>&1 "
            "| grep -iE 'ERROR|CRITICAL|traceback' "
            "| grep -vE 'Bad file descriptor|socket|SIGTERM|SIGKILL|Worker.*sent|Shutting down' "
            "| tail -5",
        )
        fa_errors = [ln for ln in out.splitlines() if ln.strip()]
        check("FastAPI no critical errors (10m)", len(fa_errors) == 0, "\n    ".join(fa_errors[:5]))

    finally:
        client.close()

    # ── Final Results ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    total = PASS_COUNT + FAIL_COUNT
    print(f"  PASSED: {PASS_COUNT}/{total}")
    if FAIL_COUNT:
        print(f"  FAILED: {FAIL_COUNT}/{total}")
        print("\n  Issues to investigate:")
        for label, detail in ISSUES:
            print(f"    ✗ {label}")
            if detail:
                print(f"      {detail[:120]}")
        print("=" * 60 + "\n")
        sys.exit(1)
    else:
        print("  ALL CHECKS PASSED ✓")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
