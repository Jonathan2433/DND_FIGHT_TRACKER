"""add character sheet metadata fields

Revision ID: 7c1a9d5f2e11
Revises: ab4d7f91c2e0
Create Date: 2026-03-18 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c1a9d5f2e11'
down_revision = 'ab4d7f91c2e0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('character_template', sa.Column('player_name', sa.String(length=100), nullable=True))
    op.add_column('character_template', sa.Column('campaign_name', sa.String(length=120), nullable=True))
    op.add_column('character_template', sa.Column('alignment', sa.String(length=60), nullable=True))
    op.add_column('character_template', sa.Column('languages', sa.String(length=255), nullable=True))
    op.add_column('character_template', sa.Column('equipment', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('character_template', 'equipment')
    op.drop_column('character_template', 'languages')
    op.drop_column('character_template', 'alignment')
    op.drop_column('character_template', 'campaign_name')
    op.drop_column('character_template', 'player_name')
