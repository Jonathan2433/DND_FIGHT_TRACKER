"""Compliance hardening backend/bdd/security.

Revision ID: 9b1f11d6a7c8
Revises: 2e6e3ec0d8a2
Create Date: 2026-03-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b1f11d6a7c8'
down_revision = '2e6e3ec0d8a2'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # EncounterTemplate ownership
    op.add_column('encounter_template', sa.Column('owner_id', sa.Integer(), nullable=True))

    first_user_id = conn.execute(sa.text('SELECT id FROM "user" ORDER BY id LIMIT 1')).scalar()
    fallback_owner_id = first_user_id if first_user_id is not None else 1

    conn.execute(
        sa.text('UPDATE encounter_template SET owner_id = :owner_id WHERE owner_id IS NULL'),
        {'owner_id': fallback_owner_id}
    )

    op.alter_column('encounter_template', 'owner_id', nullable=False)
    op.create_foreign_key(
        'fk_encounter_template_owner_id_user',
        'encounter_template',
        'user',
        ['owner_id'],
        ['id']
    )

    # JoinRequest cleanup
    with op.batch_alter_table('join_request') as batch_op:
        batch_op.drop_column('is_public')

    # Combat must be scoped to arc+campaign
    conn.execute(sa.text(
        'DELETE FROM combat WHERE story_arc_id IS NULL OR campaign_id IS NULL'
    ))

    with op.batch_alter_table('combat') as batch_op:
        batch_op.alter_column('campaign_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('story_arc_id', existing_type=sa.Integer(), nullable=False)


def downgrade():
    with op.batch_alter_table('combat') as batch_op:
        batch_op.alter_column('story_arc_id', existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column('campaign_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('join_request') as batch_op:
        batch_op.add_column(sa.Column('is_public', sa.Boolean(), nullable=True))

    op.drop_constraint('fk_encounter_template_owner_id_user', 'encounter_template', type_='foreignkey')
    op.drop_column('encounter_template', 'owner_id')
