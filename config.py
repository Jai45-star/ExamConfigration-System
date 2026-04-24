"""
config.py — Central settings via pydantic-settings.
All values are sourced from the .env file at startup.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DB_SERVER: str = "localhost"
    DB_PORT: int = 1433
    DB_NAME: str = "ExamEntryDB"
    DB_USER: str = "sa"
    DB_PASSWORD: str = ""

    # App Security
    SECRET_KEY: str = "change_me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # RSA Keys
    RSA_PRIVATE_KEY_PATH: str = "keys/private_key.pem"
    RSA_PUBLIC_KEY_PATH: str = "keys/public_key.pem"

    # Blockchain
    ETH_NODE_URL: str = ""
    ADMIN_WALLET_PRIVATE_KEY: str = ""
    CONTRACT_ADDRESS: str = ""
    CHAIN_ID: int = 11155111

    # AI Thresholds
    # Liveness: Higher means stricter anti-spoof.
    LIVENESS_THRESHOLD: float = 0.40
    # Face Match: Cosine distance threshold (lower = stricter).
    # Current value 0.43 to accommodate present environment.
    FACE_MATCH_THRESHOLD: float = 0.43

    # CORS
    FRONTEND_ORIGIN: str = "http://172.20.10.3:5500"

    # Rate Limiting
    RATE_LIMIT_VERIFY: str = "5/minute"

    @field_validator("FACE_MATCH_THRESHOLD")
    @classmethod
    def validate_face_threshold(cls, v: float) -> float:
        """Ensure threshold is in valid cosine distance range (0.0 – 1.0).
        Values > 1.0 (like 25.0) mean EVERYONE matches — a critical security flaw.
        """
        if not (0.10 <= v <= 0.50):
            raise ValueError(
                f"FACE_MATCH_THRESHOLD={v} is INVALID. "
                f"Cosine distance must be between 0.10 (strict) and 0.50 (lenient). "
                f"Recommended secure value: 0.30"
            )
        return v

    @property
    def sqlalchemy_url(self) -> str:
        import urllib.parse
        encoded_pwd = urllib.parse.quote_plus(self.DB_PASSWORD)
        return (
            f"mssql+pyodbc://{self.DB_USER}:{encoded_pwd}"
            f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
