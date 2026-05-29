-- Optional development seed data.
-- Apply after migrations:
--   psql -U comm_intel -d comm_intel_db -f backend/database/seed.sql

INSERT INTO email_archives (id, filename, file_path, status, total_emails, processed_emails)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'sample_archive.zip',
    'uploads/archives/sample_archive.zip',
    'completed',
    2,
    2
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO email_threads (
    id,
    subject_normalized,
    root_message_id,
    participant_count,
    email_count,
    first_email_at,
    last_email_at,
    summary
)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'Q1 Planning Meeting',
    'msg-root-001',
    3,
    2,
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '1 day',
    'Discussion about Q1 planning milestones and deliverables.'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO emails (
    id,
    archive_id,
    thread_id,
    message_id,
    sender,
    receivers,
    cc,
    subject,
    body_text,
    sent_at,
    summary,
    elasticsearch_id,
    chroma_id,
    source_file
)
VALUES
(
    '33333333-3333-3333-3333-333333333331',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    'msg-root-001',
    'alice@company.com',
    ARRAY['bob@company.com', 'carol@company.com'],
    ARRAY[]::TEXT[],
    'Q1 Planning Meeting',
    'Hi team, let us align on Q1 milestones and key deliverables for the communication platform.',
    NOW() - INTERVAL '2 days',
    'Alice requests Q1 planning alignment on milestones and deliverables.',
    '33333333-3333-3333-3333-333333333331',
    '33333333-3333-3333-3333-333333333331',
    'email_001.eml'
),
(
    '33333333-3333-3333-3333-333333333332',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    'msg-reply-002',
    'bob@company.com',
    ARRAY['alice@company.com', 'carol@company.com'],
    ARRAY[]::TEXT[],
    'Re: Q1 Planning Meeting',
    'Thanks Alice. I suggest we prioritize ingestion pipeline stability and dashboard analytics first.',
    NOW() - INTERVAL '1 day',
    'Bob proposes prioritizing ingestion pipeline and analytics for Q1.',
    '33333333-3333-3333-3333-333333333332',
    '33333333-3333-3333-3333-333333333332',
    'email_002.eml'
)
ON CONFLICT (id) DO NOTHING;
