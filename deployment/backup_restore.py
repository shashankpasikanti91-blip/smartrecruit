#!/usr/bin/env python3
"""Backup and restore helpers for the Docker-based ATS deployment."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


DEFAULT_DB_CONTAINER = "srp-ats-db"
DEFAULT_DB_NAME = "srp_ats"
DEFAULT_DB_USER = "srp_ats"
DEFAULT_UPLOADS_VOLUME = "srp_ats_uploads"


def run(command: list[str], cwd: Path | None = None, stdin=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        stdin=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def require_success(result: subprocess.CompletedProcess, action: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(f"{action} failed:\n{result.stderr or result.stdout}")


def backup(args: argparse.Namespace) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = args.output_dir / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_backup = backup_dir / "database.sql"
    uploads_backup = backup_dir / "uploads.tar.gz"
    manifest = backup_dir / "manifest.json"

    print(f"Creating backup in {backup_dir}")

    with db_backup.open("w", encoding="utf-8") as handle:
        result = subprocess.run(
            [
                "docker",
                "exec",
                args.db_container,
                "pg_dump",
                "-U",
                args.db_user,
                "-d",
                args.db_name,
            ],
            stdout=handle,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(f"Database backup failed:\n{result.stderr}")

    result = run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{args.uploads_volume}:/source:ro",
            "-v",
            f"{backup_dir.resolve()}:/backup",
            "alpine:3.20",
            "sh",
            "-lc",
            "cd /source && tar -czf /backup/uploads.tar.gz .",
        ]
    )
    require_success(result, "Uploads backup")

    manifest.write_text(
        json.dumps(
            {
                "created_at_utc": timestamp,
                "db_container": args.db_container,
                "db_name": args.db_name,
                "db_user": args.db_user,
                "uploads_volume": args.uploads_volume,
                "files": [db_backup.name, uploads_backup.name],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Backup complete.")


def restore(args: argparse.Namespace) -> None:
    backup_dir = args.backup_dir.resolve()
    db_backup = backup_dir / "database.sql"
    uploads_backup = backup_dir / "uploads.tar.gz"

    if not db_backup.is_file() or not uploads_backup.is_file():
        raise FileNotFoundError("Backup directory must contain database.sql and uploads.tar.gz")
    if not args.force:
        raise RuntimeError("Restore is destructive. Re-run with --force after verifying the target.")

    print(f"Restoring database from {db_backup}")
    with db_backup.open("r", encoding="utf-8") as handle:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                args.db_container,
                "psql",
                "-U",
                args.db_user,
                "-d",
                args.db_name,
            ],
            stdin=handle,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(f"Database restore failed:\n{result.stderr}")

    print(f"Restoring uploads from {uploads_backup}")
    result = run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{args.uploads_volume}:/target",
            "-v",
            f"{backup_dir}:/backup:ro",
            "alpine:3.20",
            "sh",
            "-lc",
            "rm -rf /target/* && tar -xzf /backup/uploads.tar.gz -C /target",
        ]
    )
    require_success(result, "Uploads restore")
    print("Restore complete.")


def verify(args: argparse.Namespace) -> None:
    result = run(["docker", "exec", args.db_container, "pg_isready", "-U", args.db_user, "-d", args.db_name])
    require_success(result, "Database readiness check")
    print(result.stdout.strip() or "Database is ready.")

    result = run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{args.uploads_volume}:/target:ro",
            "alpine:3.20",
            "sh",
            "-lc",
            "find /target -maxdepth 2 -type f | head -20",
        ]
    )
    require_success(result, "Uploads verification")
    print("Uploads sample:")
    print(result.stdout.strip() or "(no files found)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-container", default=DEFAULT_DB_CONTAINER)
    parser.add_argument("--db-name", default=DEFAULT_DB_NAME)
    parser.add_argument("--db-user", default=DEFAULT_DB_USER)
    parser.add_argument("--uploads-volume", default=DEFAULT_UPLOADS_VOLUME)

    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create a database and uploads backup")
    backup_parser.add_argument("--output-dir", type=Path, default=Path("backups"))
    backup_parser.set_defaults(func=backup)

    restore_parser = subparsers.add_parser("restore", help="Restore database and uploads from a backup")
    restore_parser.add_argument("backup_dir", type=Path)
    restore_parser.add_argument("--force", action="store_true")
    restore_parser.set_defaults(func=restore)

    verify_parser = subparsers.add_parser("verify", help="Verify database and uploads access")
    verify_parser.set_defaults(func=verify)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
