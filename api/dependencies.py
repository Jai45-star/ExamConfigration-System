"""
api/dependencies.py — FastAPI dependencies for Auth and DB.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import AdminUser, RevokedToken
from security.token_manager import decode_access_token
from config import get_settings
import hashlib

settings = get_settings()
security = HTTPBearer()

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """ Validates JWT and returns the current admin user. """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_TOKEN", "message": "Invalid or expired token"}
        )
    
    # Check if token is revoked
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    is_revoked = db.query(RevokedToken).filter(RevokedToken.token_hash == token_hash).first()
    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "TOKEN_REVOKED", "message": "Token has been logged out"}
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing identity")
    
    admin = db.query(AdminUser).filter(AdminUser.username == username, AdminUser.is_active == True).first()
    if admin is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found or inactive")
        
    return admin

def get_request_id(request: Request) -> str:
    """Extracts request ID inject by middleware."""
    return getattr(request.state, "request_id", "SYSTEM")
