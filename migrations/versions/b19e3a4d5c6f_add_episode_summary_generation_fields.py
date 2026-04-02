"""Add episode summary generation and email tracking fields.

Revision ID: b19e3a4d5c6f
Revises: 4f2a1d9e8b77
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b19e3a4d5c6f'
down_revision = '4f2a1d9e8b77'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'episode' not in inspector.get_table_names():
        return

    columns = {col['name'] for col in inspector.get_columns('episode')}

    if 'summary_public' not in columns:
        op.add_column('episode', sa.Column('summary_public', sa.Text(), nullable=True))

    if 'summary_generated_at' not in columns:
        op.add_column('episode', sa.Column('summary_generated_at', sa.DateTime(), nullable=True))

    if 'summary_status' not in columns:
        op.add_column(
            'episode',
            sa.Column('summary_status', sa.String(length=32), nullable=False, server_default='not_generated')
        )

    if 'summary_source_hash' not in columns:
        op.add_column('episode', sa.Column('summary_source_hash', sa.String(length=128), nullable=True))

    if 'summary_generation_error' not in columns:
        op.add_column('episode', sa.Column('summary_generation_error', sa.Text(), nullable=True))

    if 'summary_generated_by_user_id' not in columns:
        op.add_column('episode', sa.Column('summary_generated_by_user_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_episode_summary_generated_by_user_id_user',
            'episode',
            'user',
            ['summary_generated_by_user_id'],
            ['id']
        )

    if 'summary_model_name' not in columns:
        op.add_column('episode', sa.Column('summary_model_name', sa.String(length=120), nullable=True))

    if 'summary_email_status' not in columns:
        op.add_column(
            'episode',
            sa.Column('summary_email_status', sa.String(length=32), nullable=False, server_default='not_sent')
        )

    if 'summary_email_error' not in columns:
        op.add_column('episode', sa.Column('summary_email_error', sa.Text(), nullable=True))

    if 'summary_last_emailed_at' not in columns:
        op.add_column('episode', sa.Column('summary_last_emailed_at', sa.DateTime(), nullable=True))

    if 'summary_last_emailed_hash' not in columns:
        op.add_column('episode', sa.Column('summary_last_emailed_hash', sa.String(length=128), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'episode' not in inspector.get_table_names():
        return

    columns = {col['name'] for col in inspector.get_columns('episode')}
    fks = {fk['name'] for fk in inspector.get_foreign_keys('episode') if fk.get('name')}

    if 'summary_last_emailed_hash' in columns:
        op.drop_column('episode', 'summary_last_emailed_hash')

    if 'summary_last_emailed_at' in columns:
        op.drop_column('episode', 'summary_last_emailed_at')

    if 'summary_email_error' in columns:
        op.drop_column('episode', 'summary_email_error')

    if 'summary_email_status' in columns:
        op.drop_column('episode', 'summary_email_status')

    if 'summary_model_name' in columns:
        op.drop_column('episode', 'summary_model_name')

    if 'fk_episode_summary_generated_by_user_id_user' in fks:
        op.drop_constraint('fk_episode_summary_generated_by_user_id_user', 'episode', type_='foreignkey')

    if 'summary_generated_by_user_id' in columns:
        op.drop_column('episode', 'summary_generated_by_user_id')

    if 'summary_generation_error' in columns:
        op.drop_column('episode', 'summary_generation_error')

    if 'summary_source_hash' in columns:
        op.drop_column('episode', 'summary_source_hash')

    if 'summary_status' in columns:
        op.drop_column('episode', 'summary_status')

    if 'summary_generated_at' in columns:
        op.drop_column('episode', 'summary_generated_at')

    if 'summary_public' in columns:
        op.drop_column('episode', 'summary_public')
