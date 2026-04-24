"""
database/db.py — SQLAlchemy engine, session factory, and dependency.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from config import get_settings

settings = get_settings()

engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_schema(schema_sql_path: str = "database/schema.sql") -> None:
    """Execute the DDL schema file on startup (idempotent — uses IF NOT EXISTS)."""
    with open(schema_sql_path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    # Split on GO statements (T-SQL batch separator)
    batches = [b.strip() for b in raw.split("\nGO") if b.strip()]
    with engine.begin() as conn:
        for batch in batches:
            conn.execute(text(batch))
