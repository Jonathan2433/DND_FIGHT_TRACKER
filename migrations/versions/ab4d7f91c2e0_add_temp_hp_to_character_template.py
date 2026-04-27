"""add temp hp to character template

Revision ID: ab4d7f91c2e0
Revises: e12f9a7c4d11
Create Date: 2026-03-18 00:00:01.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab4d7f91c2e0'
down_revision = 'e12f9a7c4d11'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('character_template', sa.Column('temp_hp', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('character_template', 'temp_hp', server_default=None)


def downgrade():
    op.drop_column('character_template', 'temp_hp')
