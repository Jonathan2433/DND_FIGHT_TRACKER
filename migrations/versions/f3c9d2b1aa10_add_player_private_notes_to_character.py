"""add player private notes to character

Revision ID: f3c9d2b1aa10
Revises: c1b7e5a2d441
Create Date: 2026-03-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3c9d2b1aa10'
down_revision = 'c1b7e5a2d441'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('character_template', sa.Column('player_private_notes', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('character_template', 'player_private_notes')
