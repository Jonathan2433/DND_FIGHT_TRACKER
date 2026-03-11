"""Extensions Flask - Initialisation centralisée"""
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_mail import Mail

# Initialisation des extensions sans app
db = SQLAlchemy()
socketio = SocketIO()
mail = Mail()