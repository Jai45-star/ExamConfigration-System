const API_BASE = "http://localhost:8000/api";

const elements = {
    webcam: document.getElementById('webcam'),
    btnVerify: document.getElementById('btn-verify'),
    rollInput: document.getElementById('roll-number'),
    examInput: document.getElementById('exam-id'),
    statusDisplay: document.getElementById('status-display'),
    statusText: document.getElementById('status-text'),
    modalSuccess: document.getElementById('modal-success'),
    entryToken: document.getElementById('entry-token'),
    btnCloseModal: document.querySelector('.btn-close-modal')
};

// 1. Initialize Webcam
async function initWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 480, height: 360, facingMode: "user" } 
        });
        elements.webcam.srcObject = stream;
    } catch (err) {
        console.error("Camera access denied:", err);
        alert("Please allow camera access to use this system.");
    }
}

// 2. Capture Frame and Convert to Base64
function captureFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = elements.webcam.videoWidth;
    canvas.height = elements.webcam.videoHeight;
    const ctx = canvas.getContext('2d');
    
    // Draw mirrored
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(elements.webcam, 0, 0);
    
    // Return base64 (removing the "data:image/png;base64," prefix)
    return canvas.toDataURL('image/jpeg', 0.9).split(',')[1];
}

// 3. Verification Logic
elements.btnVerify.addEventListener('click', async () => {
    const roll = elements.rollInput.value.trim();
    const exam = elements.examInput.value.trim();
    
    if (!roll || !exam) {
        alert("Please enter roll number and exam ID.");
        return;
    }

    // UI Feedback
    elements.btnVerify.disabled = true;
    elements.statusDisplay.classList.remove('hidden');
    elements.statusText.textContent = "Analyzing patterns and liveness...";

    try {
        const faceB64 = captureFrame();
        
        // Use a UUIDv4 as nonce (simplified creation)
        const nonce = crypto.randomUUID();

        const response = await fetch(`${API_BASE}/entry/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                roll_number: roll,
                exam_id: exam,
                face_image_b64: faceB64,
                nonce: nonce
            })
        });

        const result = await response.json();

        if (response.ok) {
            showSuccess(result.entry_token);
        } else {
            const errorMsg = result.detail?.message || result.detail || "Verification failed";
            alert(`Error: ${errorMsg}`);
        }
    } catch (error) {
        console.error("API Error:", error);
        alert("System unavailable. Please ensure the backend is running.");
    } finally {
        elements.btnVerify.disabled = false;
        elements.statusDisplay.classList.add('hidden');
    }
});

function showSuccess(token) {
    elements.entryToken.textContent = token;
    elements.modalSuccess.classList.remove('hidden');
}

elements.btnCloseModal.addEventListener('click', () => {
    elements.modalSuccess.classList.add('hidden');
    elements.rollInput.value = "";
});

// Start
initWebcam();
