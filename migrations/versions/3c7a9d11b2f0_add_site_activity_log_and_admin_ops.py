"""add site activity log and admin ops

Revision ID: 3c7a9d11b2f0
Revises: 5df9ffc02c20, a1b2c3d4e5f6
Create Date: 2026-03-28 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c7a9d11b2f0'
down_revision = ('5df9ffc02c20', 'a1b2c3d4e5f6')
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'site_activity_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('path', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('endpoint', sa.String(length=120), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_site_activity_log_created_at'), 'site_activity_log', ['created_at'], unique=False)
    op.create_index(op.f('ix_site_activity_log_endpoint'), 'site_activity_log', ['endpoint'], unique=False)
    op.create_index(op.f('ix_site_activity_log_path'), 'site_activity_log', ['path'], unique=False)
    op.create_index(op.f('ix_site_activity_log_status_code'), 'site_activity_log', ['status_code'], unique=False)
    op.create_index(op.f('ix_site_activity_log_user_id'), 'site_activity_log', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_site_activity_log_user_id'), table_name='site_activity_log')
    op.drop_index(op.f('ix_site_activity_log_status_code'), table_name='site_activity_log')
    op.drop_index(op.f('ix_site_activity_log_path'), table_name='site_activity_log')
    op.drop_index(op.f('ix_site_activity_log_endpoint'), table_name='site_activity_log')
    op.drop_index(op.f('ix_site_activity_log_created_at'), table_name='site_activity_log')
    op.drop_table('site_activity_log')
