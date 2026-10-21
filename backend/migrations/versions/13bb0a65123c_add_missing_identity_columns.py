"""Add missing identity columns

Revision ID: 13bb0a65123c
Revises: 001_initial
Create Date: 2026-04-20 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13bb0a65123c'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to module_scores
    with op.batch_alter_table('module_scores', schema=None) as batch_op:
        batch_op.add_column(sa.Column('identity_matches', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('identity_face_matches', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('identity_risk_flags', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('identity_platforms', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('module_scores', schema=None) as batch_op:
        batch_op.drop_column('identity_platforms')
        batch_op.drop_column('identity_risk_flags')
        batch_op.drop_column('identity_face_matches')
        batch_op.drop_column('identity_matches')
