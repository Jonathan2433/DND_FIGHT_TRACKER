"""Socket event registration entrypoint."""

from .combat_events import register_socketio_events

__all__ = ["register_socketio_events"]
