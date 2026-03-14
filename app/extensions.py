"""Extensions Flask - Initialisation centralisée"""
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
socketio = SocketIO(async_mode="threading")
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()
