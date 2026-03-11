"""Factory Pattern pour l'application Flask"""
from flask import Flask, g, session
import os
from dotenv import load_dotenv

load_dotenv()

def create_app(config_name='default'):
    """Factory pour créer l'application Flask"""

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
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Initialiser les extensions
    from app.extensions import db, socketio, mail
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)


    # Importer les modèles pour que SQLAlchemy les connaisse
    from app import models

    # ✅ AJOUT : Context processor pour current_user
    @app.before_request
    def load_logged_in_user():
        """Charger l'utilisateur connecté dans g avant chaque requête"""
        user_id = session.get('user_id')

        if user_id is None:
            g.current_user = None
        else:
            from app.services.auth_service import AuthService
            g.current_user = AuthService.get_user_by_id(user_id)

    # ✅ AJOUT : Context processor pour les templates
    @app.context_processor
    def inject_user():
        """Rendre current_user disponible dans tous les templates"""
        return dict(current_user=g.get('current_user', None))

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
    from app.routes import main, combat, combatant, group, template, summary, xp
    from app.routes import auth, campaign, story_arc

    app.register_blueprint(main.bp)
    app.register_blueprint(combat.bp)
    app.register_blueprint(combatant.bp)
    app.register_blueprint(group.bp)
    app.register_blueprint(template.bp)
    app.register_blueprint(summary.bp)
    app.register_blueprint(xp.bp)
    app.register_blueprint(auth.bp)  # ✅ AJOUT LOT 1
    app.register_blueprint(campaign.bp)  # ✅ AJOUT LOT 2
    app.register_blueprint(story_arc.bp) # ✅ AJOUT LOT 3

def register_socketio_events():
    """Enregistrement des événements SocketIO"""
    from app.extensions import socketio
    from flask_socketio import join_room

    @socketio.on("join_combat")
    def handle_join(data):
        combat_id = data["combat_id"]
        join_room(f"combat_{combat_id}")