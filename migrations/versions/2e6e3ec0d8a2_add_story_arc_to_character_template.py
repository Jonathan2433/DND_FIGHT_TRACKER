"""add story arc to character template

Revision ID: 2e6e3ec0d8a2
Revises: 674e122dac1c
Create Date: 2026-03-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e6e3ec0d8a2'
down_revision = '674e122dac1c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('character_template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('story_arc_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_character_template_story_arc_id',
            'story_arc',
            ['story_arc_id'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('character_template', schema=None) as batch_op:
        batch_op.drop_constraint('fk_character_template_story_arc_id', type_='foreignkey')
        batch_op.drop_column('story_arc_id')
