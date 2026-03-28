"""Единственная точка входа: `python main.py` или `flask --app main run`."""

from app import create_app
from extensions import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
