"""merge remaining alembic heads on preprod

Revision ID: 6dd23b05f4f0
Revises: 1d3f4a9b7c21, d4c6e2a1b111
Create Date: 2026-03-20 10:44:39.684806

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6dd23b05f4f0'
down_revision = ('1d3f4a9b7c21', 'd4c6e2a1b111')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
