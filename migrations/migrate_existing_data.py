# migrations/migrate_existing_data.py
def create_admin_user():
    """Créer un utilisateur admin par défaut"""
    admin = User(
        username='admin',
        email='admin@dndtracker.local',
        password_hash=generate_password_hash('admin123'),
        role='Admin',
        is_verified=True
    )


def associate_existing_data():
    """Associer les données existantes à l'admin"""
    admin = User.query.filter_by(username='admin').first()

    # Tous les combats/personnages existants = admin
    for character in CharacterTemplate.query.all():
        character.owner_id = admin.id  # Colonne à ajouter