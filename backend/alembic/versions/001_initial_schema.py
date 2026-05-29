"""Initial database schema migration."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

archive_status_enum = postgresql.ENUM(
    "pending",
    "processing",
    "completed",
    "failed",
    name="archive_status",
    create_type=False,
)


def upgrade() -> None:
    archive_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "email_archives",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "status",
            archive_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("total_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_archives_status", "email_archives", ["status"], unique=False)

    op.create_table(
        "email_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_normalized", sa.String(length=1024), nullable=False),
        sa.Column("root_message_id", sa.String(length=512), nullable=True),
        sa.Column("participant_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("email_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_email_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_email_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_threads_subject_normalized",
        "email_threads",
        ["subject_normalized"],
        unique=False,
    )
    op.create_index(
        "ix_email_threads_root_message_id",
        "email_threads",
        ["root_message_id"],
        unique=False,
    )

    op.create_table(
        "emails",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("archive_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message_id", sa.String(length=512), nullable=True),
        sa.Column("in_reply_to", sa.String(length=512), nullable=True),
        sa.Column("references_header", sa.Text(), nullable=True),
        sa.Column("sender", sa.String(length=512), nullable=False),
        sa.Column("receivers", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("cc", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("subject", sa.String(length=1024), nullable=False, server_default=""),
        sa.Column("body_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("elasticsearch_id", sa.String(length=128), nullable=True),
        sa.Column("chroma_id", sa.String(length=128), nullable=True),
        sa.Column("source_file", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["archive_id"], ["email_archives.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thread_id"], ["email_threads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emails_archive_id", "emails", ["archive_id"], unique=False)
    op.create_index("ix_emails_thread_id", "emails", ["thread_id"], unique=False)
    op.create_index("ix_emails_message_id", "emails", ["message_id"], unique=False)
    op.create_index("ix_emails_in_reply_to", "emails", ["in_reply_to"], unique=False)
    op.create_index("ix_emails_sender", "emails", ["sender"], unique=False)
    op.create_index("ix_emails_subject", "emails", ["subject"], unique=False)
    op.create_index("ix_emails_sent_at", "emails", ["sent_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_emails_sent_at", table_name="emails")
    op.drop_index("ix_emails_subject", table_name="emails")
    op.drop_index("ix_emails_sender", table_name="emails")
    op.drop_index("ix_emails_in_reply_to", table_name="emails")
    op.drop_index("ix_emails_message_id", table_name="emails")
    op.drop_index("ix_emails_thread_id", table_name="emails")
    op.drop_index("ix_emails_archive_id", table_name="emails")
    op.drop_table("emails")

    op.drop_index("ix_email_threads_root_message_id", table_name="email_threads")
    op.drop_index("ix_email_threads_subject_normalized", table_name="email_threads")
    op.drop_table("email_threads")

    op.drop_index("ix_email_archives_status", table_name="email_archives")
    op.drop_table("email_archives")

    archive_status_enum.drop(op.get_bind(), checkfirst=True)
