"""add reminder_sent_at to campaign_session

Revision ID: 3aa7b2c9d4e1
Revises: 1d3f4a9b7c21
Create Date: 2026-03-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3aa7b2c9d4e1'
down_revision = '1d3f4a9b7c21'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('campaign_session', sa.Column('reminder_sent_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_campaign_session_reminder_sent_at'), 'campaign_session', ['reminder_sent_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_campaign_session_reminder_sent_at'), table_name='campaign_session')
    op.drop_column('campaign_session', 'reminder_sent_at')
