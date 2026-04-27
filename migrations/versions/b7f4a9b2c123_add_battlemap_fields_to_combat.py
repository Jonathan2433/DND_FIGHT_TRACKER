"""add battlemap fields to combat

Revision ID: b7f4a9b2c123
Revises: NOUVEL_ID
Create Date: 2026-03-16 10:58:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f4a9b2c123'
down_revision = '8f517a4705b3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('combat', sa.Column('battlemap_media_filename', sa.String(length=255), nullable=True))
    op.add_column('combat', sa.Column('battlemap_media_type', sa.String(length=20), nullable=True))
    op.add_column('combat', sa.Column('battlemap_tokens_json', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('combat', 'battlemap_tokens_json')
    op.drop_column('combat', 'battlemap_media_type')
    op.drop_column('combat', 'battlemap_media_filename')
