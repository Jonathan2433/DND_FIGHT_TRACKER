"""merge alembic heads after latest push

Revision ID: 94f9d5126831
Revises: 3c7a9d11b2f0, b19e3a4d5c6f
Create Date: 2026-03-28 22:57:09.373513

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94f9d5126831'
down_revision = ('3c7a9d11b2f0', 'b19e3a4d5c6f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
