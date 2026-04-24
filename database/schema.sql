-- =============================================================
-- ExamEntryDB — Full Schema (T-SQL / Microsoft SQL Server)
-- All statements are idempotent via IF NOT EXISTS guards.
-- =============================================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'ExamEntryDB')
BEGIN
    CREATE DATABASE ExamEntryDB;
END
GO

USE ExamEntryDB
GO

-- ─── Students ────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Students' AND xtype='U')
BEGIN
    CREATE TABLE Students (
        student_id          UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID() PRIMARY KEY,
        roll_number         NVARCHAR(64)        NOT NULL UNIQUE,
        full_name           NVARCHAR(256)       NOT NULL,
        exam_id             NVARCHAR(128)       NOT NULL,
        embedding_encrypted VARBINARY(MAX)      NOT NULL,
        embedding_hash      NVARCHAR(64)        NOT NULL,
        rsa_encrypted_aes_key VARBINARY(MAX)    NOT NULL,
        registered_at       DATETIME2           NOT NULL DEFAULT SYSDATETIME(),
        is_active           BIT                 NOT NULL DEFAULT 1
    );
END
GO

-- ─── ExamEntries ─────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ExamEntries' AND xtype='U')
BEGIN
    CREATE TABLE ExamEntries (
        entry_id                UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID() PRIMARY KEY,
        student_id              UNIQUEIDENTIFIER    NOT NULL REFERENCES Students(student_id),
        exam_id                 NVARCHAR(128)       NOT NULL,
        entry_token             NVARCHAR(512)       NOT NULL UNIQUE,
        token_hash              NVARCHAR(64)        NOT NULL,
        blockchain_tx_hash      NVARCHAR(128)       NULL,
        blockchain_block_number BIGINT              NULL,
        entry_timestamp         DATETIME2           NOT NULL DEFAULT SYSDATETIME(),
        ip_address              NVARCHAR(64)        NULL,
        liveness_score          FLOAT               NULL,
        face_match_score        FLOAT               NULL,
        status                  NVARCHAR(16)        NOT NULL DEFAULT 'PENDING'
                                    CHECK (status IN ('PENDING','VERIFIED','REJECTED','REVOKED')),
        is_verified             BIT                 NOT NULL DEFAULT 0,
        replay_nonce            NVARCHAR(256)       NOT NULL UNIQUE
    );
END
GO

-- ─── AdminUsers ──────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AdminUsers' AND xtype='U')
BEGIN
    CREATE TABLE AdminUsers (
        admin_id        UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID() PRIMARY KEY,
        username        NVARCHAR(128)       NOT NULL UNIQUE,
        password_hash   NVARCHAR(256)       NOT NULL,
        role            NVARCHAR(64)        NOT NULL DEFAULT 'admin',
        created_at      DATETIME2           NOT NULL DEFAULT SYSDATETIME(),
        is_active       BIT                 NOT NULL DEFAULT 1
    );
END
GO

-- ─── AuditLogs ───────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AuditLogs' AND xtype='U')
BEGIN
    CREATE TABLE AuditLogs (
        log_id      UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID() PRIMARY KEY,
        event_type  NVARCHAR(64)        NOT NULL,
        student_id  UNIQUEIDENTIFIER    NULL,
        admin_id    UNIQUEIDENTIFIER    NULL,
        description NVARCHAR(MAX)       NULL,
        ip_address  NVARCHAR(64)        NULL,
        timestamp   DATETIME2           NOT NULL DEFAULT SYSDATETIME()
    );
END
GO

-- ─── RevokedTokens ───────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RevokedTokens' AND xtype='U')
BEGIN
    CREATE TABLE RevokedTokens (
        id          UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID() PRIMARY KEY,
        token_hash  NVARCHAR(64)        NOT NULL UNIQUE,
        revoked_at  DATETIME2           NOT NULL DEFAULT SYSDATETIME()
    );
END
GO

-- ─── Indexes ─────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='IX_Students_RollNumber')
    CREATE INDEX IX_Students_RollNumber ON Students(roll_number)
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='IX_ExamEntries_Token')
    CREATE INDEX IX_ExamEntries_Token ON ExamEntries(entry_token)
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='IX_ExamEntries_StudentId')
    CREATE INDEX IX_ExamEntries_StudentId ON ExamEntries(student_id)
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='IX_ExamEntries_ExamId')
    CREATE INDEX IX_ExamEntries_ExamId ON ExamEntries(exam_id)
GO
