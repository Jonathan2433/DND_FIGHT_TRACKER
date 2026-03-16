"""Socket event handlers for user notification updates."""

from flask import session
from flask_socketio import join_room


def register_notification_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        user_id = session.get('user_id')
        if user_id:
            join_room(f'user_{user_id}')

    @socketio.on('join_notifications')
    def handle_join_notifications(_data=None):
        user_id = session.get('user_id')
        if user_id:
            join_room(f'user_{user_id}')

