"""Point d'entrée de l'application"""
from app import create_app
from app.extensions import socketio
import os

# Créer l'application
config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Lancement avec SocketIO
    socketio.run(
        app,
        debug=app.config['DEBUG'],
        host='127.0.0.1',
        port=5000
    )