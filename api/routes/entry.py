# api/routes/entry.py — Core Logic for Identity Verification and Record Entry.
import asyncio
import functools
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import cv2
import numpy as np
from datetime import datetime, timezone

from database.db import get_db
from database.models import Student, ExamEntry, AuditLog, RevokedToken, AdminUser
from api.dependencies import get_current_admin
from ai.embedding_manager import process_verification_pipeline
from security.token_manager import generate_entry_token, compute_token_hash
from blockchain.eth_client import eth_client
from utils.validators import validate_base64_image, validate_nonce
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/entry", tags=["Entry Verification"])

class VerificationRequest(BaseModel):
    roll_number: str
    exam_id: str
    face_image_b64: str
    nonce: str

@router.post("/verify")
async def verify_entry(req: VerificationRequest, request: Request, db: Session = Depends(get_db)):
    # Authenticate student identity and authorize exam entry.

    # 1. Security Nonce Validation
    if not validate_nonce(req.nonce):
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_NONCE", "message": "Security validation failed (Invalid Nonce)."})
    if db.query(ExamEntry).filter(ExamEntry.replay_nonce == req.nonce).first():
        raise HTTPException(status_code=409, detail={"error_code": "REPLAY_ATTACK", "message": "Duplicate request detected (Replay Protection)."})

    # 2. Student Identity Retrieval
    student = db.query(Student).filter(
        Student.roll_number == req.roll_number,
        Student.exam_id == req.exam_id,
        Student.is_active == True
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail={"error_code": "STUDENT_NOT_FOUND", "message": "Identity not found or account is restricted."})

    # 3. Duplicate Access Check
    if db.query(ExamEntry).filter(
        ExamEntry.student_id == student.student_id,
        ExamEntry.exam_id == req.exam_id,
        ExamEntry.status == "VERIFIED"
    ).first():
        raise HTTPException(status_code=409, detail={"error_code": "DUPLICATE_ENTRY", "message": "Access already authorized for this session."})

    # 4. Image Decoding and Validation
    image_bytes = validate_base64_image(req.face_image_b64)
    if not image_bytes:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_IMAGE", "message": "Image quality insufficient for verification."})

    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail={"error_code": "DECODE_ERROR", "message": "Processing error: Could not decode biometric data."})

    # 5. Biometric Analysis Pipeline
    try:
        with open(settings.RSA_PRIVATE_KEY_PATH, "rb") as f:
            private_key_pem = f.read()

        loop = asyncio.get_running_loop()
        pipe_fn = functools.partial(
            process_verification_pipeline,
            image_bgr,
            student.embedding_encrypted,
            student.rsa_encrypted_aes_key,
            student.embedding_hash,
            private_key_pem
        )
        pipe_result = await loop.run_in_executor(None, pipe_fn)

    except ValueError as e:
        _audit(db, "ENTRY_REJECTED", student.student_id, f"Unauthorized Attempt: {str(e)}", request.client.host)
        raise HTTPException(status_code=422, detail={"error_code": "VERIFICATION_FAILED", "message": str(e)})
    except Exception as e:
        _audit(db, "ENTRY_ERROR", student.student_id, f"System Fault: {e}", request.client.host)
        raise HTTPException(status_code=500, detail={"error_code": "AI_ERROR", "message": "Biometric analysis system error."})

    # 6. Access Token Issuance
    token = generate_entry_token(str(student.student_id), req.exam_id, pipe_result["liveness_score"])
    token_hash = compute_token_hash(token)

    # 7. Immutable Ledger Record (Blockchain Persistence)
    tx_hash, block_num = "OFF_CHAIN_SIM", 0
    try:
        if eth_client:
            ts = int(datetime.now(timezone.utc).timestamp())
            bc_fn = functools.partial(
                eth_client.record_entry_on_chain,
                req.roll_number, req.exam_id, token_hash, ts
            )
            tx_hash, block_num = await asyncio.get_running_loop().run_in_executor(None, bc_fn)
    except Exception as e:
        # Enforce blockchain persistence as a hard security requirement
        raise HTTPException(status_code=500, detail={"error_code": "BLOCKCHAIN_ERROR", "message": f"Ledger synchronization failed: {str(e)}"})

    # 8. Record persistence in Local DB
    entry_obj = ExamEntry(
        student_id=student.student_id,
        exam_id=req.exam_id,
        entry_token=token,
        token_hash=token_hash,
        blockchain_tx_hash=tx_hash,
        blockchain_block_number=block_num,
        ip_address=request.client.host,
        liveness_score=pipe_result["liveness_score"],
        face_match_score=pipe_result["face_match_score"],
        status="VERIFIED",
        is_verified=True,
        replay_nonce=req.nonce
    )
    db.add(entry_obj)
    db.flush()

    # 9. Security Audit Logging
    now_str = datetime.now().strftime("%H:%M:%S")
    _audit(db, "ENTRY_VERIFIED", student.student_id,
           f"STUDENT {student.full_name} ({student.roll_number}) ENTER IN EXAM HALL WITH TIME {now_str}", request.client.host)
    db.commit()

    return {
        "entry_id": str(entry_obj.entry_id),
        "entry_token": token,
        "blockchain_tx_hash": tx_hash,
        "blockchain_block_number": block_num,
        "student_name": student.full_name,
        "roll_number": student.roll_number,
    }

@router.get("/entries")
async def list_entries(
    exam_id: str = Query(...),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    # Retrieve authorized entry records for administrative review.
    entries = db.query(ExamEntry).filter(ExamEntry.exam_id == exam_id)\
        .order_by(ExamEntry.entry_timestamp.desc())\
        .offset((page - 1) * size).limit(size).all()
    return [{
        "entry_id": str(e.entry_id),
        "status": e.status,
        "tx_hash": e.blockchain_tx_hash,
        "match": e.face_match_score,
        "time": e.entry_timestamp.isoformat()
    } for e in entries]

def _audit(db, event_type, student_id, description, ip, admin_id=None):
    # Log internal system events for audit trails.
    db.add(AuditLog(
        event_type=event_type,
        student_id=student_id,
        admin_id=admin_id,
        description=description,
        ip_address=ip
    ))
