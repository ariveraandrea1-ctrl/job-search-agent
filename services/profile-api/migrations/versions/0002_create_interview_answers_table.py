"""crea la tabla interview_answers

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_interview_answers_telegram_user_id",
        "interview_answers",
        ["telegram_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_interview_answers_telegram_user_id", table_name="interview_answers")
    op.drop_table("interview_answers")
