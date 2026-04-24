# ai_engine/main.py — AI ka main server (Port 8001).
# Yeh server saare bhari kaam (DeepFace/TensorFlow) sambhalta hai.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import cv2
import numpy as np
import base64
import sys
import os

# Dusre folders ke modules access karne ke liye path jodna
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.face_recognition import extract_embedding
from ai.liveness_detection import compute_liveness
from ai.anti_spoof import run_anti_spoof_checks

app = FastAPI(title="AI Engine", version="1.0.0")

class ImagePayload(BaseModel):
    image_b64: str

@app.get("/health")
def health():
    return {"status": "AI Engine Online", "message": "Neural models initialized successfully."}

@app.post("/analyze")
def analyze_face(payload: ImagePayload):
    try:
        # Base64 photo ko pixels mein convert karna
        img_data = base64.b64decode(payload.image_b64)
        nparr = np.frombuffer(img_data, np.uint8)
        image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image_bgr is None:
            raise ValueError("Biometric data acquisition failed.")

        # 1. Spoof Check (Asli ya Nakli)
        is_real = run_anti_spoof_checks(image_bgr)
        if not is_real:
            return {
                "success": False, 
                "error": "Physical presence required (Proxy attempt detected).", 
                "is_spoof": True, 
                "liveness_score": 0.0, 
                "embedding": []
            }

        # 2. Liveness Check (Insaan ya Photo)
        liveness_score = float(compute_liveness(image_bgr))

        # 3. Embedding (Face features nikalna)
        embedding = extract_embedding(image_bgr)

        return {
            "success": True,
            "is_spoof": False,
            "liveness_score": liveness_score,
            "embedding": embedding
        }
    except Exception as e:
        return {"success": False, "error": f"Internal Analysis Error: {str(e)}", "liveness_score": 0.0, "embedding": []}

if __name__ == "__main__":
    import uvicorn
    # Server start karne ka command
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
