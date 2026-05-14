#!/usr/bin/env python3
"""Run the local security/readiness verification gate."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"


def run_step(label: str, command: list[str]) -> None:
    print(f"\n== {label} ==")
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed with exit code {result.returncode}")


def main() -> int:
    try:
        run_step(
            "Security regression tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "backend/tests", "-p", "test_*.py"],
        )

        import_check = (
            "import os, sys; "
            f"sys.path.insert(0, r'{BACKEND_ROOT}'); "
            "os.environ.setdefault('DATABASE_URL', 'postgresql://user:pass@localhost:5432/testdb'); "
            "os.environ.setdefault('ENVIRONMENT', 'development'); "
            "os.environ.setdefault('SEED_DEMO', 'false'); "
            "from app.main import app; "
            "print(app.title)"
        )
        run_step("App import smoke test", [sys.executable, "-c", import_check])

        if shutil.which("docker"):
            run_step("Docker Compose config", ["docker", "compose", "-f", "docker-compose.dev.yml", "config", "-q"])
        else:
            print("\n== Docker Compose config ==\nSkipping because Docker is not installed in PATH.")
        return 0
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
