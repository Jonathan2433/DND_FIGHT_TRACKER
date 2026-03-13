"""Socket event handlers for combat realtime updates."""

from flask_socketio import join_room

def register_socketio_events(socketio):
    @socketio.on("join_combat")
    def handle_join(data):
        combat_id = data["combat_id"]
        join_room(f"combat_{combat_id}")
