"""Configuration de l'application"""
import os


def _as_bool(value, default=False):
    """Convertir une variable d'environnement texte en booléen."""
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Configuration de base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Upload configuration
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.hostinger.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = _as_bool(os.environ.get('MAIL_USE_TLS'), True)
    MAIL_USE_SSL = _as_bool(os.environ.get('MAIL_USE_SSL'), False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME

    # Security
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True

TEMPLATES_AUTO_RELOAD = True

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


class PreprodConfig(ProductionConfig):
    """Préproduction: mêmes garanties que prod avec un nom d'environnement explicite."""
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'preprod': PreprodConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
