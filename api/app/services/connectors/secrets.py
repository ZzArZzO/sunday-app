"""Symmetric encryption for connector credentials at rest (Fernet).

Exchange API secrets must never be stored in plaintext. We encrypt them with a
Fernet key from settings (`connection_secret_key`) before writing `secret_enc`,
and decrypt only in-memory at sync time. Both `cryptography` and the key are
required; absent either, exchange sync stays disabled (graceful degradation).
"""

from __future__ import annotations

from app.config import get_settings
from app.services.connectors.base import ConnectorNotConfigured


def is_configured() -> bool:
    """True when secrets can be encrypted/decrypted (key set + cryptography present)."""
    if not get_settings().connection_secret_key:
        return False
    try:
        import cryptography.fernet  # noqa: F401
    except ImportError:
        return False
    return True


def _fernet():
    key = get_settings().connection_secret_key
    if not key:
        raise ConnectorNotConfigured("connection_secret_key is not set")
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise ConnectorNotConfigured("cryptography is required to store credentials") from exc
    return Fernet(key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
