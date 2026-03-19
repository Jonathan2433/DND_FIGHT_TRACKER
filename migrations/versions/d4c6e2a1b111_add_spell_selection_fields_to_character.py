"""Add spell selection fields to character template

Revision ID: d4c6e2a1b111
Revises: ee10e64e58eb
Create Date: 2026-03-19
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4c6e2a1b111'
down_revision = 'ee10e64e58eb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('character_template', sa.Column('selected_cantrips', sa.Text(), nullable=True))
    op.add_column('character_template', sa.Column('selected_level_1_spells', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('character_template', 'selected_level_1_spells')
    op.drop_column('character_template', 'selected_cantrips')
