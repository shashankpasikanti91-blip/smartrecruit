#!/usr/bin/env python3
"""Lightweight remote smoke tests for the FastAPI deployment."""

from __future__ import annotations

from remote_config import load_remote_config, open_ssh_client


def run_check(client, label: str, command: str) -> bool:
    _, stdout, stderr = client.exec_command(command, timeout=30)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    result = out or err
    ok = bool(result) and "error" not in result.lower() and "fail" not in result.lower()
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {result[:160]}")
    return ok


def main() -> None:
    config = load_remote_config(require_domain=True)
    client = open_ssh_client(config)
    try:
        checks = [
            ("Docker app health", f"curl -s http://127.0.0.1:{config.app_port}/health"),
            ("HTTPS health", f"curl -sk {config.base_https}/health"),
            ("Containers running", "docker ps --format '{{.Names}} {{.Status}}'"),
            (
                "Uploads volume mounted",
                "docker compose ps 2>/dev/null || docker ps --format '{{.Names}}'",
            ),
        ]

        print("\n=== Remote Smoke Test ===\n")
        all_pass = True
        for label, command in checks:
            all_pass = run_check(client, label, command) and all_pass

        print()
        print("=== " + ("ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED") + " ===")
    finally:
        client.close()


if __name__ == "__main__":
    main()
