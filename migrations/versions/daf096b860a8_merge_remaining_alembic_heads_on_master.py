"""merge remaining alembic heads on master

Revision ID: daf096b860a8
Revises: 1d3f4a9b7c21, d4c6e2a1b111
Create Date: 2026-03-20 10:18:30.981216

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'daf096b860a8'
down_revision = ('1d3f4a9b7c21', 'd4c6e2a1b111')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
