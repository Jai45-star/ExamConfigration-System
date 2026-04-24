# ExamSync: Biometric-Blockchain Integrated Exam Integrity System 🌿🛡️

### Presented for: Software Exhibition 2026
**Babu Banarasi Das (BBD) University, Lucknow**

---

## 🏆 Project Overview
**ExamSync** is a cutting-edge security framework designed to eliminate identity fraud (spoofing/impersonation) in high-stakes academic examinations. By merging **Advanced AI Computer Vision** with **Ethereum Blockchain Technology**, the system creates a tamper-proof digital audit trail for every student entry.

## 🚀 Key Features

### 1. Dual-Phase Biometrics (RetinaFace AI)
- **Active Liveness Detection**: Prevents 2D photo/video replay attacks using randomized motion challenges (Blink, Turn, Smile).
- **Anti-Spoofing (Glare & Texture)**: Detects pixel patterns and light reflections characteristic of mobile screens or silicone masks.
- **High-Accuracy Matching**: Uses **Facenet512** embeddings and **Cosine Similarity** to ensure 99%+ verification accuracy.

### 2. Immutable Ledger (Ethereum Sepolia)
- Every successful verification is recorded on the **Ethereum Blockchain**.
- **Tamper-Proof Audit**: Once an entry is recorded, it cannot be deleted or modified, even by the system administrator.
- **Public Verification**: Transaction hashes allow external auditors to verify entry logs via **Etherscan**.

### 3. Military-Grade Data Security
- **Hybrid Encryption**: Biometric embeddings are encrypted using **AES-256 (Symmetric)**, while the keys are protected via **RSA-2048 (Asymmetric)**.
- **Integrity Hashing**: Uses **SHA-256** to detect any manual database tampering attempt.

### 4. Professional Command Center
- **Live Telemetry**: Real-time monitoring of attendance metrics.
- **Responsive Portal**: Full support for Mobile, Tablets, and Desktop with adaptive UI for the Student Portal.

---

## 🛠️ Technology Stack
- **Backend**: Python (FastAPI, SQLAlchemy)
- **Frontend**: Vanilla Javascript, HTML5, CSS3 (Modern Glassmorphism)
- **AI Engine**: DeepFace, OpenCV, TensorFlow
- **Blockchain**: Web3.py, Solidity (Smart Contracts)
- **Infrastructure**: Ngrok (for Live Remote Access), Ethereum Sepolia Testnet

---

## 📖 Installation & Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Jai45-star/ExamConfigration-System.git
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**: Create a `.env` file with your Infura URL and Wallet private key.
4. **Run the Server**:
   ```bash
   python main.py
   ```

---

## 📜 Dev Team & Acknowledgements
Developed with passion for **BBD University, Lucknow**.  
This project demonstrates the synergy between Decentralized Finance (DeFi) technology and Educational Integrity.

**Author**: Jai Raj & Team  
**Institution**: BBD University, Lucknow
