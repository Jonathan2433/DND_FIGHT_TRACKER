"""add persistent pj combat state

Revision ID: e12f9a7c4d11
Revises: b7f4a9b2c123
Create Date: 2026-03-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e12f9a7c4d11'
down_revision = 'b7f4a9b2c123'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('character_template', sa.Column('hp_current', sa.Integer(), nullable=True))
    op.add_column('character_template', sa.Column('ac_bonus', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('combatant', sa.Column('character_template_id', sa.Integer(), nullable=True))

    op.create_foreign_key(
        'fk_combatant_character_template_id',
        'combatant',
        'character_template',
        ['character_template_id'],
        ['id']
    )

    op.execute('UPDATE character_template SET hp_current = hp_max WHERE hp_current IS NULL')
    op.alter_column('character_template', 'hp_current', nullable=False)
    op.alter_column('character_template', 'ac_bonus', server_default=None)


def downgrade():
    op.drop_constraint('fk_combatant_character_template_id', 'combatant', type_='foreignkey')
    op.drop_column('combatant', 'character_template_id')
    op.drop_column('character_template', 'ac_bonus')
    op.drop_column('character_template', 'hp_current')
