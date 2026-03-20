"""merge alembic heads

Revision ID: ee10e64e58eb
Revises: 7c1a9d5f2e11, c8f7d2a1b9aa
Create Date: 2026-03-19 12:19:47.136276

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee10e64e58eb'
down_revision = ('7c1a9d5f2e11', 'c8f7d2a1b9aa')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
