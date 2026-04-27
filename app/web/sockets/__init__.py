"""Socket event registration entrypoint."""

from .combat_events import register_socketio_events
from .notification_events import register_notification_socketio_events


def register_all_socketio_events(socketio):
    register_socketio_events(socketio)
    register_notification_socketio_events(socketio)

__all__ = ["register_all_socketio_events"]
