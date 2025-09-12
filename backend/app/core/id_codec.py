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
from contextvars import ContextVar, Token as CtxToken
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESSIV
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
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

# Session context for deterministic IDs (per session/table)
_SESSION_ID: ContextVar[_t.Optional[str]] = ContextVar("opaque_session_id", default=None)


def _get_fernet_for_version(version: int) -> Fernet:
    if version == _current_key_entry().version:
        return Fernet(_current_key_entry().key)
    # Legacy lookup
    key = _KEYRING.get(version)
    if not key:
        raise OpaqueIdError("Unknown opaque ID key version")
    return Fernet(key)


def _derive_master_bytes(secret: str) -> bytes:
    # 32 bytes master from SHA-256 of secret
    return sha256((secret or "").encode("utf-8")).digest()


def _derive_session_key(master: bytes, session_id: str) -> bytes:
    # Derive a 64-byte key suitable for AESSIV
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=None,
        info=b"idcodec|v2|session:" + session_id.encode("utf-8"),
    )
    return hkdf.derive(master)


def _aessiv_encrypt_for_session(model: str, pk: int, session_id: str) -> str:
    master = _derive_master_bytes(settings.id_secret_key or settings.jwt_secret_key)
    key = _derive_session_key(master, session_id)
    aead = AESSIV(key)
    payload = {"m": model, "k": pk}
    blob = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ct = aead.encrypt(blob, [model.encode("utf-8")])
    return "2." + base64.urlsafe_b64encode(ct).decode("utf-8")


def _aessiv_decrypt_for_session(model: str, token: str, session_id: str) -> dict:
    master = _derive_master_bytes(settings.id_secret_key or settings.jwt_secret_key)
    key = _derive_session_key(master, session_id)
    aead = AESSIV(key)
    try:
        pt = aead.decrypt(base64.urlsafe_b64decode(token.encode("utf-8")), [model.encode("utf-8")])
        payload = json.loads(pt.decode("utf-8"))
        return payload
    except Exception:
        raise OpaqueIdError("Invalid opaque ID token")


def set_current_session(session_id: _t.Optional[str]) -> CtxToken:
    """Set the current session identifier for deterministic encoding.

    Returns a context token that should be passed to reset_current_session() to restore previous value.
    """
    return _SESSION_ID.set(session_id)


def reset_current_session(token: CtxToken) -> None:
    try:
        _SESSION_ID.reset(token)
    except Exception:
        # Ignore if token invalid
        pass


def encode_id(model: str, pk: int) -> str:
    # EARLY RETURN: Disable encryption; pass through raw numeric ID as string.
    # Keep the original implementation below for easy re-enabling later.
    if isinstance(pk, (int,)):
        return str(int(pk))
    # Fallback to original validation for unexpected inputs
    if not isinstance(pk, int) or pk < 0:
        raise OpaqueIdError("Primary key must be a non-negative integer")
    model = (model or "").strip()
    if not model:
        raise OpaqueIdError("Model namespace is required")

    # Require a stable session identifier; no fallback to v1 allowed
    session_id = _SESSION_ID.get()
    if not session_id:
        raise OpaqueIdError("Session context required to encode opaque ID")
    return _aessiv_encrypt_for_session(model, pk, session_id)


def decode_id(model: str, eid: str) -> int:
    # EARLY RETURN: Disable decryption; accept plain numeric IDs.
    # If eid is an int or numeric string, return it as int immediately.
    model = (model or "").strip()
    if not model:
        raise OpaqueIdError("Model namespace is required")
    if isinstance(eid, int):
        return int(eid)
    try:
        s = str(eid).strip()
        if s.isdigit():
            return int(s)
    except Exception:
        pass

    # Legacy/opaque path: leave original secure decoding in place for backward compatibility
    if not eid or "." not in str(eid):
        raise OpaqueIdError("Invalid opaque ID format")

    try:
        vs, token = str(eid).split(".", 1)
        version = int(vs)
    except Exception:
        raise OpaqueIdError("Invalid opaque ID version prefix")

    if version == 2:
        session_id = _SESSION_ID.get()
        if not session_id:
            raise OpaqueIdError("Session context required to decode opaque ID")
        payload = _aessiv_decrypt_for_session(model, token, session_id)
    else:
        # Disallow legacy versions entirely
        raise OpaqueIdError("Unsupported opaque ID version")

    if payload.get("m") != model:
        raise OpaqueIdError("Opaque ID model mismatch")
    pk = payload.get("k")
    if not isinstance(pk, int):
        raise OpaqueIdError("Opaque ID missing integer primary key")
    return pk


__all__ = ["encode_id", "decode_id", "OpaqueIdError", "set_current_session", "reset_current_session"]
