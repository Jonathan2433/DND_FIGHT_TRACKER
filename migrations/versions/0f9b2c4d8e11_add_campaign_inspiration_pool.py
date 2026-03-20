"""add campaign inspiration pool

Revision ID: 0f9b2c4d8e11
Revises: 6dd23b05f4f0
Create Date: 2026-03-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f9b2c4d8e11'
down_revision = '6dd23b05f4f0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('campaign', sa.Column('inspiration_points', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('campaign', 'inspiration_points', server_default=None)

    op.create_table(
        'campaign_inspiration_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('episode_id', sa.Integer(), nullable=False),
        sa.Column('adjusted_by_user_id', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('previous_total', sa.Integer(), nullable=False),
        sa.Column('new_total', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['adjusted_by_user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id']),
        sa.ForeignKeyConstraint(['episode_id'], ['episode.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_campaign_inspiration_log_adjusted_by_user_id'), 'campaign_inspiration_log', ['adjusted_by_user_id'], unique=False)
    op.create_index(op.f('ix_campaign_inspiration_log_campaign_id'), 'campaign_inspiration_log', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_campaign_inspiration_log_created_at'), 'campaign_inspiration_log', ['created_at'], unique=False)
    op.create_index(op.f('ix_campaign_inspiration_log_episode_id'), 'campaign_inspiration_log', ['episode_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_campaign_inspiration_log_episode_id'), table_name='campaign_inspiration_log')
    op.drop_index(op.f('ix_campaign_inspiration_log_created_at'), table_name='campaign_inspiration_log')
    op.drop_index(op.f('ix_campaign_inspiration_log_campaign_id'), table_name='campaign_inspiration_log')
    op.drop_index(op.f('ix_campaign_inspiration_log_adjusted_by_user_id'), table_name='campaign_inspiration_log')
    op.drop_table('campaign_inspiration_log')

    op.drop_column('campaign', 'inspiration_points')
