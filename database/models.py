"""
database/models.py — SQLAlchemy ORM models.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float, BigInteger,
    LargeBinary, ForeignKey, Text, CheckConstraint
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Student(Base):
    __tablename__ = "Students"

    student_id            = Column(UNIQUEIDENTIFIER, primary_key=True, default=_uuid)
    roll_number           = Column(String(64), nullable=False, unique=True, index=True)
    full_name             = Column(String(256), nullable=False)
    exam_id               = Column(String(128), nullable=False)
    embedding_encrypted   = Column(LargeBinary, nullable=False)
    embedding_hash        = Column(String(64), nullable=False)
    rsa_encrypted_aes_key = Column(LargeBinary, nullable=False)
    registered_at         = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active             = Column(Boolean, nullable=False, default=True)

    entries = relationship("ExamEntry", back_populates="student")


class ExamEntry(Base):
    __tablename__ = "ExamEntries"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','VERIFIED','REJECTED','REVOKED')", name="ck_entry_status"),
    )

    entry_id               = Column(UNIQUEIDENTIFIER, primary_key=True, default=_uuid)
    student_id             = Column(UNIQUEIDENTIFIER, ForeignKey("Students.student_id"), nullable=False, index=True)
    exam_id                = Column(String(128), nullable=False, index=True)
    entry_token            = Column(String(512), nullable=False, unique=True)
    token_hash             = Column(String(64), nullable=False)
    blockchain_tx_hash     = Column(String(128), nullable=True)
    blockchain_block_number= Column(BigInteger, nullable=True)
    entry_timestamp        = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address             = Column(String(64), nullable=True)
    liveness_score        = Column(Float, nullable=True)
    face_match_score       = Column(Float, nullable=True)
    status                 = Column(String(16), nullable=False, default="PENDING")
    is_verified            = Column(Boolean, nullable=False, default=False)
    replay_nonce           = Column(String(256), nullable=False, unique=True)

    student = relationship("Student", back_populates="entries")


class AdminUser(Base):
    __tablename__ = "AdminUsers"

    admin_id      = Column(UNIQUEIDENTIFIER, primary_key=True, default=_uuid)
    username      = Column(String(128), nullable=False, unique=True)
    password_hash = Column(String(256), nullable=False)
    role          = Column(String(64), nullable=False, default="admin")
    created_at    = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active     = Column(Boolean, nullable=False, default=True)


class AuditLog(Base):
    __tablename__ = "AuditLogs"

    log_id      = Column(UNIQUEIDENTIFIER, primary_key=True, default=_uuid)
    event_type  = Column(String(64), nullable=False)
    student_id  = Column(UNIQUEIDENTIFIER, nullable=True)
    admin_id    = Column(UNIQUEIDENTIFIER, nullable=True)
    description = Column(Text, nullable=True)
    ip_address  = Column(String(64), nullable=True)
    timestamp   = Column(DateTime, nullable=False, default=datetime.utcnow)


class RevokedToken(Base):
    __tablename__ = "RevokedTokens"

    id         = Column(UNIQUEIDENTIFIER, primary_key=True, default=_uuid)
    token_hash = Column(String(64), nullable=False, unique=True)
    revoked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
