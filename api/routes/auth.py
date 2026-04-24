"""
api/routes/auth.py — Admin authentication routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib

from database.db import get_db
from database.models import AdminUser, RevokedToken, AuditLog
from security.hashing import verify_password
from security.token_manager import create_access_token
from api.dependencies import security, get_current_admin, get_request_id

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/admin/login")
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticates admin and returns JWT."""
    admin = db.query(AdminUser).filter(AdminUser.username == req.username, AdminUser.is_active == True).first()
    
    if not admin or not verify_password(req.password, admin.password_hash):
        # Log failed attempt
        log = AuditLog(
            event_type="ADMIN_LOGIN_FAILED",
            description=f"Failed login attempt for username: {req.username}",
            ip_address=request.client.host
        )
        db.add(log)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTH_FAILED", "message": "Invalid username or password"}
        )

    access_token = create_access_token(data={"sub": admin.username})
    
    # Log success
    log = AuditLog(
        event_type="ADMIN_LOGIN_SUCCESS",
        admin_id=admin.admin_id,
        description=f"Admin {admin.username} logged in",
        ip_address=request.client.host
    )
    db.add(log)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/admin/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Revokes the current JWT by storing its hash."""
    token = credentials.credentials
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Check if already revoked
    existing = db.query(RevokedToken).filter(RevokedToken.token_hash == token_hash).first()
    if not existing:
        revocation = RevokedToken(token_hash=token_hash)
        db.add(revocation)
        
        log = AuditLog(
            event_type="ADMIN_LOGOUT",
            admin_id=current_admin.admin_id,
            description=f"Admin {current_admin.username} logged out",
            ip_address=request.client.host
        )
        db.add(log)
        db.commit()
    
    return {"message": "Logged out successfully"}

@router.get("/admin/verify-token")
async def verify_token(current_admin: AdminUser = Depends(get_current_admin)):
    """Validates token and returns admin identity."""
    return {
        "admin_id": str(current_admin.admin_id),
        "username": current_admin.username,
        "role": current_admin.role
    }
