"""merge remaining alembic heads on master

Revision ID: d00f92c1c3d0
Revises: 0f9b2c4d8e11, 65c5efef76f2, daf096b860a8
Create Date: 2026-03-20 20:53:30.280190

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd00f92c1c3d0'
down_revision = ('0f9b2c4d8e11', '65c5efef76f2', 'daf096b860a8')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
