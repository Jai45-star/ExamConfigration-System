"""
ai/face_recognition.py — DeepFace embedding extraction and distance calculation.
"""
from typing import List, Tuple
import numpy as np
import logging
from deepface import DeepFace

logger = logging.getLogger("AI_FACE")


def extract_embedding(image_bgr: np.ndarray) -> List[float]:
    """
    Extract a 512-dimensional face embedding using DeepFace.
    Triple-Fallback system for poor lighting/mobile cameras.
    """
    detectors = ["retinaface", "opencv", "mediapipe"]
    
    for detector in detectors:
        try:
            logger.info(f"Attempting detection with {detector}...")
            results = DeepFace.represent(
                img_path=image_bgr,
                model_name="Facenet512",
                detector_backend=detector,
                enforce_detection=True,
                align=True,
            )
            if results:
                logger.info(f"Detection successful with {detector}")
                return results[0]["embedding"]
        except Exception:
            continue

    # Final Attempt: Blind attempt (Relaxed)
    logger.warning("All primary detectors failed. Attempting low-strictness recovery...")
    try:
        results = DeepFace.represent(
            img_path=image_bgr,
            model_name="Facenet512",
            detector_backend="opencv",
            enforce_detection=False,
            align=True,
        )
        if results:
            return results[0]["embedding"]
    except Exception as e:
        raise ValueError("Face not found: Please stabilize your phone and try to face a light source.")
    
    raise ValueError("Biometric signal lost. Please ensure your face is at least partially visible.")


def verify_faces(
    source_emb: List[float], target_emb: List[float], threshold: float = 0.35
) -> Tuple[bool, float, float, float]:
    """
    Compute Cosine distance between two embeddings.
    Cosine distance = 1 - (A . B / (||A|| * ||B||))
    Returns: (is_match, distance, confidence_score, threshold)
    """
    if len(source_emb) != 512 or len(target_emb) != 512:
        raise ValueError("Both embeddings must be 512-dimensional.")
    
    a = np.array(source_emb, dtype=np.float32)
    b = np.array(target_emb, dtype=np.float32)
    
    # Cosine Similarity calculation
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return False, 1.0, 0.0, threshold

    similarity = dot_product / (norm_a * norm_b)
    distance = 1.0 - float(similarity)
    
    # Cosine distance 0 means identical, 1 means completely different (or 2 if opposite)
    # Recommended threshold for Facenet512 (Cosine) is usually between 0.30 and 0.40
    is_match = distance <= threshold
    
    # Confidence calculation (Inverted distance)
    confidence = max(0.0, min(1.0, 1.0 - distance))
    
    return is_match, distance, confidence, threshold
