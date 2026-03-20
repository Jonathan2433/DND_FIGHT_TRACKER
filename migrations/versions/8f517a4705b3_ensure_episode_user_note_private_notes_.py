from alembic import op
import sqlalchemy as sa


revision = "8f517a4705b3"
down_revision = "5df9ffc02c20"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "episode_user_note" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("episode_user_note")}
    if "private_notes" not in columns:
        op.add_column(
            "episode_user_note",
            sa.Column("private_notes", sa.Text(), nullable=True)
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "episode_user_note" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("episode_user_note")}
    if "private_notes" in columns:
        op.drop_column("episode_user_note", "private_notes")