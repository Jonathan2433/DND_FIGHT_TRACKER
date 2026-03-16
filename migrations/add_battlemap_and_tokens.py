"""Migration manuelle: battle map + tokens + profils monstres."""
from sqlalchemy import text
from app import create_app
from app.extensions import db


def has_column(table_name, column_name):
    result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
    return any(row[1] == column_name for row in result.fetchall())


def table_exists(table_name):
    result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"), {'name': table_name})
    return result.fetchone() is not None


app = create_app('development')

with app.app_context():
    if not has_column('combat', 'battlemap_media_filename'):
        db.session.execute(text('ALTER TABLE combat ADD COLUMN battlemap_media_filename VARCHAR(255)'))
    if not has_column('combat', 'battlemap_media_type'):
        db.session.execute(text('ALTER TABLE combat ADD COLUMN battlemap_media_type VARCHAR(20)'))

    if not has_column('combatant', 'token_image_filename'):
        db.session.execute(text('ALTER TABLE combatant ADD COLUMN token_image_filename VARCHAR(255)'))
    if not has_column('combatant', 'map_x'):
        db.session.execute(text('ALTER TABLE combatant ADD COLUMN map_x FLOAT DEFAULT 50.0'))
    if not has_column('combatant', 'map_y'):
        db.session.execute(text('ALTER TABLE combatant ADD COLUMN map_y FLOAT DEFAULT 50.0'))

    if not table_exists('monster_profile'):
        db.session.execute(text('''
            CREATE TABLE monster_profile (
                id INTEGER PRIMARY KEY,
                monster_name VARCHAR(100) UNIQUE NOT NULL,
                image_filename VARCHAR(255) NOT NULL
            )
        '''))

    db.session.commit()
    print('Migration battle map appliquée.')
