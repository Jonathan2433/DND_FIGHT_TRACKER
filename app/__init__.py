"""Factory Pattern pour l'application Flask"""
from flask import Flask
import os

def create_app(config_name='default'):
    """Factory pour créer l'application Flask"""

    # ✅ CORRECTION : Créer l'instance Flask avec le bon chemin des templates
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    # Configuration
    from config import config
    app.config.from_object(config[config_name])

    # Créer le dossier d'upload s'il n'existe pas
    upload_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app.config['UPLOAD_FOLDER']))
    os.makedirs(upload_folder, exist_ok=True)

    # ✅ MISE À JOUR : Corriger le chemin d'upload aussi
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Initialiser les extensions
    from app.extensions import db, socketio
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Importer les modèles pour que SQLAlchemy les connaisse
    from app import models

    # Enregistrer les Blueprints
    register_blueprints(app)

    # Enregistrer les gestionnaires d'événements SocketIO
    register_socketio_events()

    # Créer les tables en mode développement
    if config_name == 'development':
        with app.app_context():
            db.create_all()

    return app

def register_blueprints(app):
    """Enregistrement de tous les blueprints"""

    # Import ici pour éviter les imports circulaires
    from app.routes import main, combat, combatant, group, template, summary

    # ✅ Enregistrer TOUS les blueprints maintenant
    app.register_blueprint(main.bp)
    app.register_blueprint(combat.bp)
    app.register_blueprint(combatant.bp)
    app.register_blueprint(group.bp)
    app.register_blueprint(template.bp)
    app.register_blueprint(summary.bp)

def register_socketio_events():
    """Enregistrement des événements SocketIO"""
    from app.extensions import socketio
    from flask_socketio import join_room

    @socketio.on("join_combat")
    def handle_join(data):
        combat_id = data["combat_id"]
        join_room(f"combat_{combat_id}")