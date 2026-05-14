#!/usr/bin/env python3
"""Remote deployment helper for the checked-in FastAPI service."""

from __future__ import annotations

import sys

from remote_config import load_remote_config, open_ssh_client


def run_step(client, label: str, command: str, timeout: int = 180) -> str:
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    _, stdout, stderr = client.exec_command(command, timeout=timeout, get_pty=False)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err:
        print(f"[stderr] {err[:800]}")
    return out


def main() -> None:
    config = load_remote_config()
    commands = [
        (
            "Pull latest code",
            f"cd {config.project_dir} && git fetch origin && git pull --ff-only",
        ),
        (
            "Rebuild and restart app",
            f"cd {config.project_dir} && docker compose up -d --build",
        ),
        (
            "Check local app health",
            f"sleep 5 && curl -sf http://127.0.0.1:{config.app_port}/health",
        ),
        (
            "Reload nginx if present",
            "sudo systemctl reload nginx 2>/dev/null || echo 'nginx reload skipped'",
        ),
    ]

    print("=== SRP SmartRecruit Remote Deploy ===")
    print(f"Connecting to {config.user}@{config.host}:{config.port}")
    if config.ssh_key_path:
        print(f"Using SSH key: {config.ssh_key_path}")
    else:
        print("Using password authentication because SRP_ALLOW_PASSWORD_AUTH=true")

    try:
        client = open_ssh_client(config)
    except Exception as exc:
        print(f"SSH connect failed: {exc}")
        sys.exit(1)

    print("Connected.")
    try:
        for label, command in commands:
            run_step(client, label, command)
    finally:
        client.close()

    print("\n" + "=" * 60)
    print("Deploy completed.")
    if config.domain:
        print(f"Health URL: https://{config.domain}/health")
    print("=" * 60)


if __name__ == "__main__":
    main()
