"""add private notes to episode user note

Revision ID: a7d9c1ef42b3
Revises: f3c9d2b1aa10
Create Date: 2026-03-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7d9c1ef42b3'
down_revision = 'f3c9d2b1aa10'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('episode_user_note', sa.Column('private_notes', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('episode_user_note', 'private_notes')
