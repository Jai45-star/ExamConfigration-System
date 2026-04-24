"""
utils/logger.py — Centralised structured logging via loguru.
Never log raw embeddings, raw keys, or full stack traces in responses.
"""
import sys
from loguru import logger


def configure_logger() -> None:
    logger.remove()
    # Console — human-readable
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
        level="INFO",
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
    # Rotating file — full detail (never expose to API)
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} — {message}",
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    # Separate audit log file
    logger.add(
        "logs/audit_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | AUDIT | {message}",
        level="INFO",
        filter=lambda r: "AUDIT" in r["extra"],
        enqueue=True,
    )


def get_logger(name: str):
    return logger.bind(source=name)


audit_logger = logger.bind(AUDIT=True)
