"""initial_schema

Revision ID: 48825e83cd6b
Revises:
Create Date: 2026-06-21 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "48825e83cd6b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("anesthesiologist", "validator", name="user_role"),
            nullable=False,
            server_default="anesthesiologist",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # simulation_sessions
    op.create_table(
        "simulation_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scenario_id", sa.String(255), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("current_state_id", sa.String(255), nullable=False),
        sa.Column("current_vitals", sa.JSON, nullable=False),
        sa.Column("sim_time_seconds", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("time_in_current_state_seconds", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("is_terminal", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("outcome_id", sa.String(255), nullable=True),
    )

    # action_log_entries
    op.create_table(
        "action_log_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("simulation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entry_id", sa.String(255), nullable=False),
        sa.Column("sim_time_seconds", sa.Float, nullable=False),
        sa.Column("action_id", sa.String(255), nullable=False),
        sa.Column("action_label", sa.String(500), nullable=False),
        sa.Column("state_before", sa.String(255), nullable=False),
        sa.Column("state_after", sa.String(255), nullable=False),
        sa.Column("effect_summary", sa.Text, nullable=False),
    )
    op.create_index("ix_action_log_session", "action_log_entries", ["session_id"])

    # clinical_validations
    op.create_table(
        "clinical_validations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scenario_id", sa.String(255), nullable=False),
        sa.Column("rule_ref", sa.String(500), nullable=False),
        sa.Column("rule_description", sa.Text, nullable=False),
        sa.Column(
            "validated_by_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "validated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("clinical_validations")
    op.drop_index("ix_action_log_session", table_name="action_log_entries")
    op.drop_table("action_log_entries")
    op.drop_table("simulation_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role")
