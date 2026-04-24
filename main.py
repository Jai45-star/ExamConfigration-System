# main.py — Yeh humari app ka main entry point hai.
import uvicorn
import uuid
import asyncio
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_settings
from database.db import run_schema
from security.encryption import generate_rsa_keypair
from api.routes import auth, student, admin, entry
from utils.logger import configure_logger, get_logger

settings = get_settings()

# Log folder check karna taaki system fail na ho
os.makedirs("logs", exist_ok=True)
configure_logger()
logger = get_logger(__name__)

# Rate limit set karna taaki koi server crash na kar sake
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server start ho raha hai...")
    app.state.loop = asyncio.get_running_loop()
    os.makedirs("keys", exist_ok=True)

    # Agar security keys (RSA) purani nahi hain toh nayi banana
    if not os.path.exists(settings.RSA_PRIVATE_KEY_PATH):
        logger.info("Nayi security keys ban rahi hain...")
        generate_rsa_keypair(settings.RSA_PRIVATE_KEY_PATH, settings.RSA_PUBLIC_KEY_PATH)

    # Database ke tables check karna aur deploy karna
    try:
        logger.info("Database schema check ho raha hai...")
        run_schema()
        logger.info("Database ekdum sahi hai.")
    except Exception as e:
        logger.error(f"Database setup mein error aaya: {e}")

    logger.info("Server ready hai address http://0.0.0.0:8000 par!")
    yield
    logger.info("Server band ho raha hai.")

# Main app configuration
app = FastAPI(
    title="Exam Entry System",
    description="Face recognition aur Blockchain based exam hall security.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Sabhi jagah se entry allow karna (CORS setting)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Har request ko track karna aur time napna
@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response

# Agar kisi wajah se koi badi error aaye toh use gracefully handle karna
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "UNKNOWN")
    logger.exception(f"Ek anjaan server error aayi [req={req_id}]: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Kuch gadbad ho gayi hai, please administrator se baat karein.",
            "request_id": req_id,
        },
    )

# Saare pages aur functions (Routes) ko jorna
app.include_router(auth.router,    prefix="/api")
app.include_router(student.router, prefix="/api")
app.include_router(admin.router,   prefix="/api")
app.include_router(entry.router,   prefix="/api")

# Health check
@app.get("/api/health", tags=["Health"])
async def root():
    return {"status": "ok", "message": "System operational hai."}

# Serve Frontend - Must be last!
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    # Server chalane ka command
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
