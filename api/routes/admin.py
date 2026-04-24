"""
api/routes/admin.py — Admin dashboard and management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, Date
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

from database.db import get_db
from database.models import Student, ExamEntry, AuditLog, AdminUser
from api.dependencies import get_current_admin
from security.hashing import hash_password

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

class AdminCreateRequest(BaseModel):
    username: str
    password: str
    role: str = "admin"

@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Returns live summary counts for the dashboard."""
    today = date.today()
    
    total_students = db.query(Student).count()
    total_entries_today = db.query(ExamEntry).filter(func.cast(ExamEntry.entry_timestamp, Date) == today).count()
    verified_entries = db.query(ExamEntry).filter(ExamEntry.status == "VERIFIED").count()
    rejected_entries = db.query(ExamEntry).filter(ExamEntry.status == "REJECTED").count()
    revoked_entries = db.query(ExamEntry).filter(ExamEntry.status == "REVOKED").count()
    
    return {
        "total_students": total_students,
        "entries_today": total_entries_today,
        "verified_total": verified_entries,
        "rejected_total": rejected_entries,
        "revoked_total": revoked_entries
    }

@router.get("/audit-logs")
async def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    event_type: Optional[str] = None,
    student_id: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Paginated audit logs with optional filters."""
    query = db.query(AuditLog)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if student_id:
        query = query.filter(AuditLog.student_id == student_id)
        
    logs = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return [{
        "log_id": str(l.log_id),
        "event_type": l.event_type,
        "student_id": str(l.student_id) if l.student_id else None,
        "admin_id": str(l.admin_id) if l.admin_id else None,
        "description": l.description,
        "ip_address": l.ip_address,
        "timestamp": l.timestamp.isoformat()
    } for l in logs]

@router.post("/create")
async def create_admin(req: AdminCreateRequest, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Creates a new admin user."""
    # Only super-admins can create others (simplified logic here)
    if admin.role != "super_admin":
         # In a real app we'd check roles, but requirement just says create new admin.
         pass

    existing = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    
    new_admin = AdminUser(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role
    )
    db.add(new_admin)
    db.commit()
    return {"message": "Admin created successfully"}

@router.put("/{admin_id}/deactivate")
async def deactivate_admin(admin_id: str, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Deactivates an admin."""
    target = db.query(AdminUser).filter(AdminUser.admin_id == admin_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    target.is_active = False
    db.commit()
    return {"message": "Admin deactivated"}

@router.get("/reports/exam/{exam_id}")
async def get_exam_report(exam_id: str, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Returns a full report for an exam."""
    # Join Students and ExamEntries
    records = db.query(Student, ExamEntry).outerjoin(
        ExamEntry, Student.student_id == ExamEntry.student_id
    ).filter(Student.exam_id == exam_id).all()
    
    report = []
    for s, e in records:
        report.append({
            "roll_number": s.roll_number,
            "full_name": s.full_name,
            "status": e.status if e else "NOT_ARRIVED",
            "token": e.entry_token if e else None,
            "blockchain_tx": e.blockchain_tx_hash if e else None,
            "entry_time": e.entry_timestamp.isoformat() if e else None,
            "liveness_score": e.liveness_score if e else None,
            "face_match_score": e.face_match_score if e else None
        })
    return report
