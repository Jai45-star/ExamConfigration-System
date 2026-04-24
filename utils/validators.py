"""
utils/validators.py — Input validation helpers.
"""
import re
import base64
import uuid
from typing import Optional


def validate_roll_number(roll: str) -> bool:
    """Alpha-numeric, 3–32 chars."""
    return bool(re.match(r"^[A-Za-z0-9/_-]{3,32}$", roll))


def validate_exam_id(exam_id: str) -> bool:
    """Alpha-numeric + hyphens, 3–64 chars."""
    return bool(re.match(r"^[A-Za-z0-9_-]{3,64}$", exam_id))


def validate_base64_image(b64: str) -> Optional[bytes]:
    """
    Decode a base64 (or data-URI encoded) image.
    Returns raw bytes on success, None on failure.
    """
    try:
        if b64.startswith("data:"):
            # Strip data-URI prefix: data:image/jpeg;base64,<data>
            b64 = b64.split(",", 1)[1]
        return base64.b64decode(b64)
    except Exception:
        return None


def validate_nonce(nonce: str) -> bool:
    """Nonce must be a valid UUID4 string."""
    try:
        val = uuid.UUID(nonce, version=4)
        return str(val) == nonce.lower()
    except ValueError:
        return False


def sanitise_string(value: str, max_len: int = 256) -> str:
    """Strip control characters and truncate."""
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", value)
    return cleaned[:max_len]
