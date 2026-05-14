#!/usr/bin/env python3
"""Shared remote deployment configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import paramiko


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class RemoteConfig:
    host: str
    user: str
    port: int
    project_dir: str
    domain: str | None
    app_port: int
    ssh_key_path: str | None
    ssh_password: str | None
    allow_password_auth: bool

    @property
    def base_https(self) -> str | None:
        if not self.domain:
            return None
        return f"https://{self.domain}"


def load_remote_config(require_domain: bool = False) -> RemoteConfig:
    host = os.getenv("SRP_DEPLOY_HOST")
    if not host:
        raise RuntimeError("Set SRP_DEPLOY_HOST before running remote deployment scripts.")

    domain = os.getenv("SRP_DEPLOY_DOMAIN")
    if require_domain and not domain:
        raise RuntimeError("Set SRP_DEPLOY_DOMAIN before running this script.")

    ssh_key_path = os.getenv("SRP_DEPLOY_KEY_PATH")
    ssh_password = os.getenv("SRP_DEPLOY_PASSWORD")
    allow_password_auth = _env_flag("SRP_ALLOW_PASSWORD_AUTH", default=False)

    if not ssh_key_path and not (allow_password_auth and ssh_password):
        raise RuntimeError(
            "Set SRP_DEPLOY_KEY_PATH to a trusted SSH private key. "
            "Password auth is only allowed when SRP_ALLOW_PASSWORD_AUTH=true "
            "and SRP_DEPLOY_PASSWORD is set."
        )

    return RemoteConfig(
        host=host,
        user=os.getenv("SRP_DEPLOY_USER", "deploy"),
        port=int(os.getenv("SRP_DEPLOY_PORT", "22")),
        project_dir=os.getenv("SRP_PROJECT_DIR", "/opt/srp-ats"),
        domain=domain,
        app_port=int(os.getenv("SRP_APP_PORT", "8009")),
        ssh_key_path=str(Path(ssh_key_path).expanduser()) if ssh_key_path else None,
        ssh_password=ssh_password,
        allow_password_auth=allow_password_auth,
    )


def open_ssh_client(config: RemoteConfig) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())

    connect_kwargs = {
        "hostname": config.host,
        "port": config.port,
        "username": config.user,
        "timeout": 20,
    }

    if config.ssh_key_path:
        connect_kwargs["key_filename"] = config.ssh_key_path
        connect_kwargs["allow_agent"] = True
        connect_kwargs["look_for_keys"] = False
    else:
        connect_kwargs["password"] = config.ssh_password
        connect_kwargs["allow_agent"] = False
        connect_kwargs["look_for_keys"] = False

    client.connect(**connect_kwargs)
    return client
