"""add campaign sessions calendar

Revision ID: 1d3f4a9b7c21
Revises: c1b7e5a2d441
Create Date: 2026-03-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d3f4a9b7c21'
down_revision = 'c1b7e5a2d441'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'campaign_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False),
        sa.Column('is_cancelled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_campaign_session_campaign_id'), 'campaign_session', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_campaign_session_scheduled_for'), 'campaign_session', ['scheduled_for'], unique=False)
    op.create_index(op.f('ix_campaign_session_is_cancelled'), 'campaign_session', ['is_cancelled'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_campaign_session_is_cancelled'), table_name='campaign_session')
    op.drop_index(op.f('ix_campaign_session_scheduled_for'), table_name='campaign_session')
    op.drop_index(op.f('ix_campaign_session_campaign_id'), table_name='campaign_session')
    op.drop_table('campaign_session')
