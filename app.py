from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for
from flask_login import current_user
from flask_socketio import emit, join_room

from i18n import (
    DEFAULT_LOCALE,
    client_status_label,
    client_type_label,
    gettext,
    js_strings_json,
    normalize_locale,
    role_label,
)
from extensions import db, login_manager, socketio


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "avishu.db"


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
    login_manager.login_message = gettext(DEFAULT_LOCALE, "login_required")
    login_manager.localize_callback = lambda: gettext(
        normalize_locale(request.cookies.get("av_lang")),
        "login_required",
    )

    from models import User
    from routes.auth import auth_bp
    from routes.client import client_bp
    from routes.franchisee import franchisee_bp
    from routes.production import production_bp
    from routes.orders_api import orders_api_bp
    from routes.theme import theme_bp
    from routes.locale_route import locale_bp
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

    @app.context_processor
    def cart_count():
        if not current_user.is_authenticated:
            return {"cart_count": 0}
        if getattr(current_user, "role", None) != "client":
            return {"cart_count": 0}
        cart = session.get("cart")
        n = len(cart) if isinstance(cart, list) else 0
        return {"cart_count": n}

    @app.context_processor
    def theme_context():
        t = request.cookies.get("av_theme", "light")
        if t not in ("light", "dark"):
            t = "light"
        lang = normalize_locale(request.cookies.get("av_lang"))
        def _t(key: str, **kwargs):
            return gettext(lang, key, **kwargs)

        return {
            "theme_mode": t,
            "body_theme_class": "av-theme-dark" if t == "dark" else "",
            "locale": lang,
            "html_lang": lang,
            "t": _t,
            "js_i18n": js_strings_json(lang),
            "next_lang": "kk" if lang == DEFAULT_LOCALE else DEFAULT_LOCALE,
            "label_order_type": lambda ot: client_type_label(lang, ot),
            "label_order_status": lambda st: client_status_label(lang, st),
            "label_role": lambda r: role_label(lang, r),
        }

    app.register_blueprint(theme_bp)
    app.register_blueprint(locale_bp)
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