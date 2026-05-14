#!/usr/bin/env python3
"""Upload `system_prompts.txt` to a remote FastAPI deployment."""

from __future__ import annotations

from pathlib import Path
import os

from remote_config import load_remote_config, open_ssh_client


def main() -> None:
    config = load_remote_config()
    local_file = Path(os.getenv("SRP_LOCAL_PROMPTS_FILE", Path(__file__).resolve().parents[1] / "backend" / "system_prompts.txt"))
    if not local_file.is_file():
        raise FileNotFoundError(f"Local prompts file not found: {local_file}")

    client = open_ssh_client(config)
    try:
        print("Connected to server")
        sftp = client.open_sftp()
        remote_path = f"{config.project_dir}/backend/system_prompts.txt"
        try:
            sftp.put(str(local_file), remote_path)
            print(f"Uploaded prompts to {remote_path}")
        finally:
            sftp.close()

        _, stdout, stderr = client.exec_command(
            f"cd {config.project_dir} && docker compose restart app 2>&1 && echo RESTART_OK",
            timeout=60,
        )
        print("Restart:\n", stdout.read().decode(errors="replace") + stderr.read().decode(errors="replace"))

        _, stdout, _ = client.exec_command(
            f"sleep 5 && curl -s http://127.0.0.1:{config.app_port}/health",
            timeout=30,
        )
        print("FastAPI health:", stdout.read().decode(errors="replace").strip())
    finally:
        client.close()

    print("Done")


if __name__ == "__main__":
    main()
