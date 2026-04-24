# ai/embedding_manager.py — AI Engine aur Backend ke beech ka bridge.
import numpy as np
import base64
import cv2
import httpx
from typing import Dict, Any, List
from security.encryption import generate_aes_key, encrypt_aes_cbc, decrypt_aes_cbc, encrypt_rsa_oaep, decrypt_rsa_oaep
from security.hashing import compute_sha256, verify_sha256
from ai.face_recognition import verify_faces
from config import get_settings

settings = get_settings()
AI_ENGINE_URL = "http://localhost:8001/analyze"

def _call_ai_engine(image_bgr: np.ndarray) -> Dict[str, Any]:
    # Dusre server (Port 8001) par photo bhejkar facial analysis karwana.
    _, buffer = cv2.imencode(".jpg", image_bgr)
    img_b64 = base64.b64encode(buffer).decode("utf-8")
    
    # Timeout None rakha hai taaki model load hone mein time lage toh server wait kare
    with httpx.Client(timeout=None) as client:
        try:
            response = client.post(AI_ENGINE_URL, json={"image_b64": img_b64})
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise ValueError(f"Unable to communicate with AI Engine: {str(e)}")

        if not result.get("success"):
            # Pass through logical errors directly
            raise ValueError(result.get("error", "AI Analysis Engine rejected request."))
        
        return result

def process_registration_pipeline(image_bgr: np.ndarray, public_key_pem: bytes) -> Dict[str, Any]:
    # Naye student ko register karne wala process.
    ai_result = _call_ai_engine(image_bgr)
    
    embedding = ai_result["embedding"]
    liveness_score = ai_result["liveness_score"]
    
    # Liveness check karna
    if liveness_score < settings.LIVENESS_THRESHOLD:
         raise ValueError(f"Detection failed: Identity requires live presence (Score: {liveness_score:.2f})")

    embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
    
    # Data ko encrypt (lock) karna taaki koi chura na sake
    aes_key = generate_aes_key()
    encrypted_embedding = encrypt_aes_cbc(embedding_bytes, aes_key)
    encrypted_aes_key = encrypt_rsa_oaep(aes_key, public_key_pem)
    embedding_hash = compute_sha256(embedding_bytes)
    
    return {
        "embedding_encrypted": encrypted_embedding,
        "embedding_hash": embedding_hash,
        "rsa_encrypted_aes_key": encrypted_aes_key,
        "liveness_score": liveness_score
    }

def process_verification_pipeline(
    live_image_bgr: np.ndarray, 
    stored_encrypted_embedding: bytes,
    stored_encrypted_aes_key: bytes,
    stored_embedding_hash: str,
    private_key_pem: bytes
) -> Dict[str, Any]:
    # Entry par student ka face check karne wala process.
    ai_result = _call_ai_engine(live_image_bgr)
    
    live_embedding = ai_result["embedding"]
    liveness_score = ai_result["liveness_score"]
    
    if liveness_score < settings.LIVENESS_THRESHOLD:
        raise ValueError(f"Presence verification failed (Score: {liveness_score:.2f})")

    # Database se purana data nikal kar unlock karna
    aes_key = decrypt_rsa_oaep(stored_encrypted_aes_key, private_key_pem)
    stored_embedding_bytes = decrypt_aes_cbc(stored_encrypted_embedding, aes_key)
    
    # Check karna ki data ke saath koi chhed-chhad toh nahi hui
    if not verify_sha256(stored_embedding_bytes, stored_embedding_hash):
        raise ValueError("Security Violation: Identity profile tamper detected.")
    
    stored_embedding = np.frombuffer(stored_embedding_bytes, dtype=np.float32).tolist()
    
    # Purane face aur naye face ko compare karna
    is_match, distance, confidence, threshold = verify_faces(
        stored_embedding, live_embedding, threshold=settings.FACE_MATCH_THRESHOLD
    )
    
    from utils.logger import get_logger
    logger = get_logger("AI_VERIFY")

    margin = threshold - distance  # positive = safe gap, negative = should be rejected
    if not is_match:
        logger.warning(
            f"FACE MISMATCH REJECTED — Distance={distance:.4f} > Threshold={threshold} | "
            f"Person is NOT the registered student."
        )
    elif margin < 0.05:
        logger.warning(
            f"BORDERLINE MATCH — Distance={distance:.4f}, Threshold={threshold}, Margin={margin:.4f} "
            f"(Very close to rejection boundary!)"
        )
    else:
        logger.success(
            f"FACE VERIFIED — Distance={distance:.4f} (Threshold={threshold}, Safe Margin={margin:.4f})"
        )

    if not is_match:
        raise ValueError(f"Identity mismatch: Biometric similarity threshold not met (Dist: {distance:.2f})")
    
    return {
        "liveness_score": liveness_score,
        "face_match_score": confidence,
        "match_distance": distance
    }
