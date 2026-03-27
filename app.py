from pathlib import Path

from flask import Flask, redirect, render_template, url_for
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "avishu.db"

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(async_mode="threading")


def create_app(test_config=None):
    app = Flask(__name__, instance_path=str(INSTANCE_DIR), instance_relative_config=True)
    app.config["SECRET_KEY"] = "change-me-for-production"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if test_config:
        app.config.update(test_config)

    if not app.config.get("TESTING"):
        INSTANCE_DIR.mkdir(exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Авторизуйтесь, чтобы продолжить."

    from models import User
    from routes.auth import auth_bp
    from routes.client import client_bp
    from routes.franchisee import franchisee_bp
    from routes.production import production_bp
    from routes.orders_api import orders_api_bp
    from routes.helpers import redirect_for_role

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect_for_role()
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("403.html"), 403

    app.register_blueprint(auth_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(franchisee_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(orders_api_bp)

    with app.app_context():
        db.create_all()

    return app


@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:
        return False

    join_room(f"user:{current_user.id}")
    join_room(f"role:{current_user.role}")
    emit(
        "connected",
        {
            "message": "SocketIO connected",
            "user_id": current_user.id,
            "role": current_user.role,
        },
    )


@socketio.on("ping_server")
def handle_ping(data=None):
    emit(
        "pong_server",
        {
            "message": "pong",
            "payload": data or {},
        },
    )


app = create_app()


if __name__ == "__main__":
    socketio.run(app, debug=True)
