"""Initial schema — reflects current ProfileIQ database

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id",       sa.Integer(),  nullable=False),
        sa.Column("email",    sa.String(),   nullable=False),
        sa.Column("password", sa.String(),   nullable=False),
        sa.Column("role",     sa.String(),   nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id",    "users", ["id"],    unique=False)

    op.create_table(
        "analyses",
        sa.Column("id",                sa.Integer(),  nullable=False),
        sa.Column("user_id",           sa.Integer(),  nullable=True),
        sa.Column("profile_url",       sa.String(),   nullable=False),
        sa.Column("input_type",        sa.String(),   nullable=True),
        sa.Column("profile_image_b64", sa.Text(),     nullable=True),
        sa.Column("trust_score",       sa.Float(),    nullable=True),
        sa.Column("confidence",        sa.Float(),    nullable=True),
        sa.Column("risk_level",        sa.String(),   nullable=True),
        sa.Column("summary",           sa.Text(),     nullable=True),
        sa.Column("created_at",        sa.DateTime(), nullable=True),
        sa.Column("ocr_platform",      sa.String(),   nullable=True),
        sa.Column("ocr_username",      sa.String(),   nullable=True),
        sa.Column("ocr_bio",           sa.Text(),     nullable=True),
        sa.Column("ocr_followers",     sa.String(),   nullable=True),
        sa.Column("ocr_following",     sa.String(),   nullable=True),
        sa.Column("ocr_posts",         sa.String(),   nullable=True),
        sa.Column("ocr_confidence",    sa.Float(),    nullable=True),
        sa.Column("ocr_raw_text",      sa.Text(),     nullable=True),
        sa.Column("ocr_error",         sa.String(),   nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyses_id", "analyses", ["id"], unique=False)

    op.create_table(
        "module_scores",
        sa.Column("id",                     sa.Integer(), nullable=False),
        sa.Column("analysis_id",            sa.Integer(), nullable=True),
        sa.Column("face_score",             sa.Float(),   nullable=True),
        sa.Column("text_score",             sa.Float(),   nullable=True),
        sa.Column("behavior_score",         sa.Float(),   nullable=True),
        sa.Column("network_score",          sa.Float(),   nullable=True),
        sa.Column("consistency_score",      sa.Float(),   nullable=True),
        sa.Column("identity_score",         sa.Float(),   nullable=True),
        sa.Column("face_age",               sa.Integer(), nullable=True),
        sa.Column("face_gender",            sa.String(),  nullable=True),
        sa.Column("face_emotion",           sa.String(),  nullable=True),
        sa.Column("face_flags",             sa.String(),  nullable=True),
        sa.Column("face_source",            sa.String(),  nullable=True),
        sa.Column("text_classification",    sa.String(),  nullable=True),
        sa.Column("text_scam_prob",         sa.Float(),   nullable=True),
        sa.Column("text_ai_prob",           sa.Float(),   nullable=True),
        sa.Column("text_flags",             sa.String(),  nullable=True),
        sa.Column("text_scam_keywords",     sa.Text(),    nullable=True),
        sa.Column("text_source",            sa.String(),  nullable=True),
        sa.Column("behavior_anomaly_score", sa.Float(),   nullable=True),
        sa.Column("behavior_flags",         sa.String(),  nullable=True),
        sa.Column("behavior_source",        sa.String(),  nullable=True),
        sa.Column("profile_type",           sa.String(),  nullable=True),
        sa.Column("profile_entities",       sa.Text(),    nullable=True),
        sa.Column("profile_summary",        sa.Text(),    nullable=True),
        sa.Column("profile_type_confidence",sa.Float(),   nullable=True),
        sa.Column("identity_matches",       sa.Integer(), nullable=True),
        sa.Column("identity_face_matches",  sa.Integer(), nullable=True),
        sa.Column("identity_risk_flags",    sa.String(),  nullable=True),
        sa.Column("identity_platforms",     sa.String(),  nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_module_scores_id", "module_scores", ["id"], unique=False)

    op.create_table(
        "evidence_logs",
        sa.Column("id",          sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=True),
        sa.Column("log_type",    sa.String(),  nullable=True),
        sa.Column("module",      sa.String(),  nullable=True),
        sa.Column("message",     sa.Text(),    nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_logs_id", "evidence_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("evidence_logs")
    op.drop_table("module_scores")
    op.drop_table("analyses")
    op.drop_table("users")
