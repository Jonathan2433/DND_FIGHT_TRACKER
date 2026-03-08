"""Extensions Flask - Initialisation centralisée"""
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Initialisation des extensions sans app
db = SQLAlchemy()
socketio = SocketIO()