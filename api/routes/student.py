"""
api/routes/student.py — Student registration and management.
BUG FIX: /search route MUST be declared before /{student_id} to avoid
         FastAPI treating 'search' as a student_id path param.
"""
import asyncio
import functools
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import cv2
import numpy as np
from typing import Optional

from database.db import get_db
from database.models import Student, AuditLog, AdminUser
from api.dependencies import get_current_admin
from ai.embedding_manager import process_registration_pipeline
from utils.validators import validate_roll_number, validate_exam_id, validate_base64_image
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/students", tags=["Students"])


class StudentRegisterRequest(BaseModel):
    roll_number: str
    full_name: str
    exam_id: str
    face_image_b64: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_student(
    req: StudentRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Registers a new student — runs AI pipeline + AES/RSA encryption."""
    if not validate_roll_number(req.roll_number):
        raise HTTPException(status_code=400, detail="Invalid roll number format")
    if not validate_exam_id(req.exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID format")

    if db.query(Student).filter(Student.roll_number == req.roll_number).first():
        raise HTTPException(status_code=409, detail="Roll number already registered")

    image_bytes = validate_base64_image(req.face_image_b64)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Invalid base64 image")

    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    try:
        with open(settings.RSA_PUBLIC_KEY_PATH, "rb") as f:
            public_key_pem = f.read()

        loop = asyncio.get_running_loop()
        fn = functools.partial(process_registration_pipeline, image_bgr, public_key_pem)
        result = await loop.run_in_executor(None, fn)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"error_code": "AI_REGISTRATION_ERROR", "message": str(e)})
    except Exception:
        raise HTTPException(status_code=500, detail="Internal AI processing error")

    new_student = Student(
        roll_number=req.roll_number,
        full_name=req.full_name,
        exam_id=req.exam_id,
        embedding_encrypted=result["embedding_encrypted"],
        embedding_hash=result["embedding_hash"],
        rsa_encrypted_aes_key=result["rsa_encrypted_aes_key"]
    )
    db.add(new_student)
    db.flush()

    db.add(AuditLog(
        event_type="STUDENT_REGISTERED",
        student_id=new_student.student_id,
        admin_id=admin.admin_id,
        description=f"Registered {req.full_name} ({req.roll_number}) for exam {req.exam_id}",
        ip_address=request.client.host
    ))
    db.commit()
    return {"student_id": str(new_student.student_id), "message": "Registered successfully"}


@router.get("/")
async def list_students(
    page: int = 1,
    size: int = 20,
    q: Optional[str] = Query(None, description="Search by name or roll number"),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Paginated student list with optional search."""
    query = db.query(Student)
    if q:
        query = query.filter(
            (Student.roll_number.ilike(f"%{q}%")) | 
            (Student.full_name.ilike(f"%{q}%"))
        )
    
    rows = query.order_by(Student.registered_at.desc()).offset((page - 1) * size).limit(size).all()
    return [_fmt(s) for s in rows]


# ── FIX: /search MUST come before /{student_id} ──────────────────────────────
@router.get("/search")
async def search_student(
    roll_number: str = Query(..., description="Exact roll number to search for"),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Exact search by roll number."""
    student = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _fmt(student)


@router.get("/{student_id}")
async def get_student(
    student_id: str,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Fetch one student by UUID."""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _fmt(student)


@router.delete("/{student_id}")
async def deactivate_student(
    student_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Soft-delete: marks student inactive."""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_active = False
    db.add(AuditLog(
        event_type="STUDENT_DEACTIVATED",
        student_id=student.student_id,
        admin_id=admin.admin_id,
        description=f"Student {student.roll_number} deactivated by {admin.username}",
        ip_address=request.client.host
    ))
    db.commit()
    return {"message": "Student deactivated"}


def _fmt(s: Student) -> dict:
    """Safe serialisation — never exposes raw embedding."""
    return {
        "student_id": str(s.student_id),
        "roll_number": s.roll_number,
        "full_name": s.full_name,
        "exam_id": s.exam_id,
        "registered_at": s.registered_at.isoformat(),
        "is_active": s.is_active,
    }
