"""
Secret Service — SRP SmartRecruit v4.0
AES-256 encryption / decryption for connector credentials
"""

from __future__ import annotations
import base64
import hashlib
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Key derivation — uses SECRET_KEY from environment (required in production)
# ─────────────────────────────────────────────────────────────────────────────

def _derive_key() -> bytes:
    secret = os.getenv("SECRET_KEY", "")
    if not secret or len(secret) < 16:
        raise EnvironmentError(
            "SECRET_KEY env var must be set and at least 16 characters for credential encryption"
        )
    return hashlib.sha256(secret.encode()).digest()   # 32 bytes → AES-256


# ─────────────────────────────────────────────────────────────────────────────
# Encrypt / Decrypt
# ─────────────────────────────────────────────────────────────────────────────

def encrypt_secret(plaintext: str) -> str:
    """
    Encrypt a plaintext secret using AES-256-CBC.
    Returns a base64-encoded string of IV + ciphertext.
    Falls back to XOR-based obfuscation if pycryptodome is unavailable,
    but logs a warning — production should always have pycryptodome installed.
    """
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        key = _derive_key()
        iv  = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ct     = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
        return base64.b64encode(iv + ct).decode()
    except ImportError:
        logger.warning(
            "pycryptodome not installed — falling back to base64 obfuscation. "
            "Install pycryptodome for production encryption."
        )
        return base64.b64encode(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a secret encrypted by encrypt_secret."""
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        key     = _derive_key()
        raw     = base64.b64decode(ciphertext)
        iv, ct  = raw[:16], raw[16:]
        cipher  = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size).decode()
    except ImportError:
        return base64.b64decode(ciphertext).decode()
    except Exception as exc:
        logger.error("Failed to decrypt secret: %s", exc)
        raise ValueError("Unable to decrypt credential. Key may have changed.") from exc


def mask_secret(plaintext: str) -> str:
    """Return a UI-safe masked version: ••••••••{last 4 chars}"""
    if len(plaintext) <= 4:
        return "••••"
    return "••••••••" + plaintext[-4:]


def build_key_hint(plaintext: str) -> str:
    return mask_secret(plaintext)
