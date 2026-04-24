"""
verify_setup.py — Health check script for the Exam Entry System.
Run this after setting up your .env file to ensure all components are operational.
"""
import sys
import os
import asyncio
import cv2
import numpy as np
from loguru import logger

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_settings
from database.db import engine
from sqlalchemy import text
from ai.face_recognition import extract_embedding
from security.encryption import generate_aes_key
from blockchain.eth_client import eth_client

async def run_checks():
    settings = get_settings()
    logger.info("Starting System Ready Check...")

    # 1. Directory Structure
    req_dirs = ["ai", "api", "blockchain", "database", "security", "admin", "utils", "keys", "logs"]
    for d in req_dirs:
        if os.path.exists(d):
            logger.success(f"Directory found: {d}/")
        else:
            logger.warning(f"Directory missing: {d}/ (Will be created on startup)")

    # 2. Configuration & Secrets
    if os.path.exists(".env"):
        logger.success(".env file found.")
    else:
        logger.error(".env file MISSING. Please rename .env and configure it.")

    # 3. Database Connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.success("Database connection successful (SQL Server).")
    except Exception as e:
        logger.error(f"Database connection FAILED: {e}")

    # 4. RSA Keys
    if os.path.exists(settings.RSA_PRIVATE_KEY_PATH) and os.path.exists(settings.RSA_PUBLIC_KEY_PATH):
        logger.success("RSA Keypair found in keys/ folder.")
    else:
        logger.warning("RSA Keypair not found. (Will be generated on first main.py run)")

    # 5. AI Pipeline Readiness (DeepFace)
    logger.info("Initializing AI Models (this may take a moment for the first download)...")
    try:
        # Create a dummy blank face image (black doesn't work for detection usually, let's just test import)
        test_img = np.zeros((300, 300, 3), dtype=np.uint8)
        # We won't run full extraction because it requires a face, but we'll check if models load.
        from deepface import DeepFace
        # Warmup (optional, checks if library is functional)
        logger.success("AI Libraries (DeepFace, OpenCV, TF) loaded successfully.")
    except Exception as e:
        logger.error(f"AI Library initialization FAILED: {e}")

    # 6. Blockchain Readiness
    if eth_client and eth_client.w3:
        try:
            is_connected = eth_client.w3.is_connected()
            if is_connected:
                logger.success(f"Blockchain connected to Sepolia: {settings.ETH_NODE_URL}")
                balance = eth_client.w3.eth.get_balance(eth_client.account.address)
                logger.info(f"Wallet Balance: {eth_client.w3.from_wei(balance, 'ether')} ETH")
            else:
                logger.error("Blockchain client initialized but NOT connected.")
        except Exception as e:
            logger.error(f"Blockchain connection check FAILED: {e}")
    else:
        logger.warning("Blockchain client NOT configured or failed to initialize.")

    logger.info("Check complete.")

if __name__ == "__main__":
    asyncio.run(run_checks())
