"""Add episodes and bind combats to episodes.

Revision ID: 4f2a1d9e8b77
Revises: 9b1f11d6a7c8
Create Date: 2026-03-15
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f2a1d9e8b77'
down_revision = '9b1f11d6a7c8'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    op.create_table(
        'episode',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_arc_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('summary_shared', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['story_arc_id'], ['story_arc.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'episode_user_note',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('episode_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['episode_id'], ['episode.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('episode_id', 'user_id', name='uq_episode_note_episode_user')
    )

    op.add_column('combat', sa.Column('episode_id', sa.Integer(), nullable=True))

    arc_rows = conn.execute(sa.text('SELECT id, name FROM story_arc ORDER BY id')).fetchall()
    for arc_id, arc_name in arc_rows:
        episode_id = conn.execute(
            sa.text(
                'INSERT INTO episode (story_arc_id, title, summary_shared, order_index, created_at) '
                'VALUES (:story_arc_id, :title, :summary_shared, 0, CURRENT_TIMESTAMP)'
            ),
            {
                'story_arc_id': arc_id,
                'title': f'Episode 1 - {arc_name}',
                'summary_shared': None,
            }
        ).lastrowid

        conn.execute(
            sa.text('UPDATE combat SET episode_id = :episode_id WHERE story_arc_id = :story_arc_id'),
            {'episode_id': episode_id, 'story_arc_id': arc_id}
        )

    conn.execute(sa.text('DELETE FROM combat WHERE episode_id IS NULL'))

    with op.batch_alter_table('combat') as batch_op:
        batch_op.alter_column('episode_id', existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key('fk_combat_episode_id_episode', 'episode', ['episode_id'], ['id'])


def downgrade():
    with op.batch_alter_table('combat') as batch_op:
        batch_op.drop_constraint('fk_combat_episode_id_episode', type_='foreignkey')
        batch_op.drop_column('episode_id')

    op.drop_table('episode_user_note')
    op.drop_table('episode')
