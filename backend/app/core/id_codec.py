"""
Centralized opaque ID codec using authenticated encryption (Option B).

- encode_id(model: str, pk: int) -> str
- decode_id(model: str, eid: str) -> int

Uses Fernet (AES128-CBC + HMAC via cryptography) with a version prefix to support
future key rotation. Output is URL-safe.

Security notes:
- Tokens are bound to the `model` namespace so a token for one model cannot be
  reused for another.
- Failures raise OpaqueIdError; callers should generally return 404.
"""
from __future__ import annotations

import base64
import json
import os
import typing as _t
from dataclasses import dataclass
from cryptography.fernet import Fernet, InvalidToken
from hashlib import sha256

from app.core.config import settings


class OpaqueIdError(Exception):
    pass


@dataclass(frozen=True)
class _KeyEntry:
    version: int
    key: bytes  # fernet key (base64 32-byte key)


def _derive_fernet_key_from_secret(secret: str) -> bytes:
    """
    Accepts either a raw 32-byte base64 fernet key, or derives a fernet key
    from an arbitrary secret by hashing to 32 bytes and base64-encoding.
    """
    s = secret.strip()
    # If it looks like a Fernet key (urlsafe base64, 32 bytes when decoded), use directly
    try:
        raw = base64.urlsafe_b64decode(s)
        if len(raw) == 32:
            return base64.urlsafe_b64encode(raw)
    except Exception:
        pass
    # Derive from arbitrary secret with SHA-256
    digest = sha256(s.encode("utf-8")).digest()  # 32 bytes
    return base64.urlsafe_b64encode(digest)


def _current_key_entry() -> _KeyEntry:
    # Prefer explicit id_secret_key; fall back to jwt_secret_key (derived)
    secret = settings.id_secret_key or settings.jwt_secret_key
    fkey = _derive_fernet_key_from_secret(secret)
    return _KeyEntry(version=int(getattr(settings, "id_codec_version", 1)), key=fkey)


# In future, we could maintain a keyring keyed by version.
_KEYRING: dict[int, bytes] = { }


def _get_fernet_for_version(version: int) -> Fernet:
    if version == _current_key_entry().version:
        return Fernet(_current_key_entry().key)
    # Legacy lookup
    key = _KEYRING.get(version)
    if not key:
        # As a convenience, allow fallback to current key if versions match by default
        raise OpaqueIdError("Unknown opaque ID key version")
    return Fernet(key)


def encode_id(model: str, pk: int) -> str:
    if not isinstance(pk, int) or pk < 0:
        raise OpaqueIdError("Primary key must be a non-negative integer")
    model = (model or "").strip()
    if not model:
        raise OpaqueIdError("Model namespace is required")

    entry = _current_key_entry()
    payload = {
        "m": model,  # model namespace
        "k": pk,     # integer pk
    }
    blob = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    token = _get_fernet_for_version(entry.version).encrypt(blob)
    # Prefix with version and a dot, e.g., "1." + token
    return f"{entry.version}." + token.decode("utf-8")


def decode_id(model: str, eid: str) -> int:
    model = (model or "").strip()
    if not model:
        raise OpaqueIdError("Model namespace is required")
    if not eid or "." not in eid:
        raise OpaqueIdError("Invalid opaque ID format")

    try:
        vs, token = eid.split(".", 1)
        version = int(vs)
    except Exception:
        raise OpaqueIdError("Invalid opaque ID version prefix")

    try:
        data = _get_fernet_for_version(version).decrypt(token.encode("utf-8"), ttl=None)
        payload = json.loads(data.decode("utf-8"))
    except InvalidToken:
        raise OpaqueIdError("Invalid opaque ID token")
    except Exception:
        raise OpaqueIdError("Malformed opaque ID payload")

    if payload.get("m") != model:
        raise OpaqueIdError("Opaque ID model mismatch")
    pk = payload.get("k")
    if not isinstance(pk, int):
        raise OpaqueIdError("Opaque ID missing integer primary key")
    return pk


__all__ = ["encode_id", "decode_id", "OpaqueIdError"]
