"""Factory Pattern pour l'application Flask"""
from flask import Flask, g, session
import os
from dotenv import load_dotenv

load_dotenv()


def create_app(config_name='default'):
    """Factory pour créer l'application Flask"""

    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # Configuration
    from config import config
    app.config.from_object(config[config_name])

    # Créer le dossier d'upload s'il n'existe pas
    upload_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', app.config['UPLOAD_FOLDER'])
    )
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Initialiser les extensions
    from app.extensions import db, socketio, mail, migrate, csrf
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Importer les modèles pour que SQLAlchemy les connaisse
    from app import models

    @app.before_request
    def load_logged_in_user():
        """Charger l'utilisateur connecté dans g avant chaque requête"""
        user_id = session.get('user_id')

        if user_id is None:
            g.current_user = None
        else:
            from app.application.use_cases.auth_service import AuthService
            g.current_user = AuthService.get_user_by_id(user_id)

    @app.context_processor
    def inject_user():
        """Rendre current_user et ses notifications disponibles dans tous les templates"""
        current_user = g.get('current_user', None)
        unread_notifications_count = 0
        header_notifications = []

        if current_user:
            from app.application.use_cases.notification_service import NotificationService
            unread_notifications_count = NotificationService.unread_count(current_user.id)
            header_notifications = NotificationService.list_user_notifications(current_user.id, limit=6)

        return dict(
            current_user=current_user,
            unread_notifications_count=unread_notifications_count,
            header_notifications=header_notifications,
        )

    register_blueprints(app)
    register_socketio_events()

    return app


def register_blueprints(app):
    """Enregistrement des blueprints via le web layer."""
    from app.web.routes import register_blueprints as register_web_blueprints
    register_web_blueprints(app)


def register_socketio_events():
    """Enregistrement des événements SocketIO via le web layer."""
    from app.extensions import socketio
    from app.web.sockets import register_socketio_events as register_web_socket_events
    register_web_socket_events(socketio)
