"""Flask extensions (no app factory) — avoids circular imports with models."""

from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(async_mode="threading")
