"""add roleplay fields to character template

Revision ID: a1b2c3d4e5f6
Revises: d82b54fe7507
Create Date: 2026-03-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd82b54fe7507'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('character_template', sa.Column('personality_traits', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('ideals', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('bonds', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('flaws', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('inspiration', sa.Boolean(), nullable=True, server_default='false'))


def downgrade():
    op.drop_column('character_template', 'inspiration')
    op.drop_column('character_template', 'flaws')
    op.drop_column('character_template', 'bonds')
    op.drop_column('character_template', 'ideals')
    op.drop_column('character_template', 'personality_traits')
