"""merge remaining alembic heads on preprod

Revision ID: d82b54fe7507
Revises: 3aa7b2c9d4e1, d00f92c1c3d0
Create Date: 2026-03-20 22:02:15.916021

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd82b54fe7507'
down_revision = ('3aa7b2c9d4e1', 'd00f92c1c3d0')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
