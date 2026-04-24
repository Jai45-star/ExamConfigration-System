"""
security/hashing.py — Direct bcrypt hashing to avoid passlib environment bugs.
"""
import hashlib
import bcrypt

def hash_password(password: str) -> str:
    """Hashes a password using direct bcrypt."""
    # Use direct bcrypt library to bypass passlib's bug detection
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def compute_sha256(data: bytes) -> str:
    """Computes SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()

def verify_sha256(data: bytes, expected_hash: str) -> bool:
    """Verifies SHA-256 hash of raw bytes."""
    return compute_sha256(data) == expected_hash
