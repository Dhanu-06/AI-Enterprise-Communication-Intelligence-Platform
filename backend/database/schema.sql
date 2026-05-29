-- PostgreSQL schema for AI Enterprise Communication Intelligence Platform
-- Prefer Alembic migrations for application schema changes.
-- This file is a reference snapshot aligned with 001_initial_schema.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TYPE archive_status AS ENUM ('pending', 'processing', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS email_archives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(512) NOT NULL,
    file_path VARCHAR(1024) NOT NULL,
    status archive_status NOT NULL DEFAULT 'pending',
    total_emails INTEGER NOT NULL DEFAULT 0,
    processed_emails INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_email_archives_status ON email_archives (status);

CREATE TABLE IF NOT EXISTS email_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_normalized VARCHAR(1024) NOT NULL,
    root_message_id VARCHAR(512),
    participant_count INTEGER NOT NULL DEFAULT 0,
    email_count INTEGER NOT NULL DEFAULT 0,
    first_email_at TIMESTAMPTZ,
    last_email_at TIMESTAMPTZ,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_email_threads_subject_normalized ON email_threads (subject_normalized);
CREATE INDEX IF NOT EXISTS ix_email_threads_root_message_id ON email_threads (root_message_id);

CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    archive_id UUID NOT NULL REFERENCES email_archives (id) ON DELETE CASCADE,
    thread_id UUID REFERENCES email_threads (id) ON DELETE SET NULL,
    message_id VARCHAR(512),
    in_reply_to VARCHAR(512),
    references_header TEXT,
    sender VARCHAR(512) NOT NULL,
    receivers TEXT[] NOT NULL DEFAULT '{}',
    cc TEXT[] NOT NULL DEFAULT '{}',
    subject VARCHAR(1024) NOT NULL DEFAULT '',
    body_text TEXT NOT NULL DEFAULT '',
    body_html TEXT,
    sent_at TIMESTAMPTZ,
    summary TEXT,
    elasticsearch_id VARCHAR(128),
    chroma_id VARCHAR(128),
    source_file VARCHAR(1024),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_emails_archive_id ON emails (archive_id);
CREATE INDEX IF NOT EXISTS ix_emails_thread_id ON emails (thread_id);
CREATE INDEX IF NOT EXISTS ix_emails_message_id ON emails (message_id);
CREATE INDEX IF NOT EXISTS ix_emails_in_reply_to ON emails (in_reply_to);
CREATE INDEX IF NOT EXISTS ix_emails_sender ON emails (sender);
CREATE INDEX IF NOT EXISTS ix_emails_subject ON emails (subject);
CREATE INDEX IF NOT EXISTS ix_emails_sent_at ON emails (sent_at);
