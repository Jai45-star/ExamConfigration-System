"""
security/token_manager.py — HMAC-SHA256 entry tokens and JWT auth.
BUG FIX: hmac.new() does not exist → correct call is hmac.new() which
in Python 3 is accessed as hmac.new() — actually it IS valid via
the internal C implementation. However, we use the standard-library 
approach: hmac.new(key, msg, digestmod) which IS correct Python.
"""
import hmac as _hmac
import hashlib
import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from config import get_settings

settings = get_settings()


def generate_entry_token(student_id: str, exam_id: str, liveness_score: float) -> str:
    """
    Generates a unique HMAC-SHA256 signed entry token.
    Returns: base64url(payload) + "." + base64url(signature)
    """
    payload = {
        "student_id": student_id,
        "exam_id": exam_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "jti": str(uuid.uuid4()),
        "liveness_score": round(liveness_score, 6)
    }

    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip("=")

    # FIX: correct HMAC call using _hmac.new (stdlib alias)
    mac = _hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    )
    signature_b64 = base64.urlsafe_b64encode(mac.digest()).decode().rstrip("=")

    return f"{payload_b64}.{signature_b64}"


def compute_token_hash(token: str) -> str:
    """Computes SHA-256 hash of the full token string."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── Admin JWT Logic ──────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT for admin authentication."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT. Returns None on any failure."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
