"""Flask extensions (no app factory) — avoids circular imports with models."""

from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
# simple-websocket нужен для нормального WebSocket в async_mode=threading (см. requirements.txt)
socketio = SocketIO(
    async_mode="threading",
    cors_allowed_origins="*",
)
