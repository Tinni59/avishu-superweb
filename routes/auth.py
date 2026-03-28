from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from i18n import flash_message, normalize_locale
from extensions import db
from models import USER_ROLES, User
from routes.helpers import redirect_for_role

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    loc = normalize_locale(request.cookies.get("av_lang"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash(flash_message(loc, "flash_wrong_credentials"), "error")
            return render_template("auth/login.html")

        login_user(user)
        flash(flash_message(loc, "flash_login_ok"), "success")
        return redirect_for_role()

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    loc = normalize_locale(request.cookies.get("av_lang"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()

        if not email or not password or role not in USER_ROLES:
            flash(flash_message(loc, "flash_register_fields"), "error")
            return render_template("auth/register.html", roles=USER_ROLES)

        if User.query.filter_by(email=email).first():
            flash(flash_message(loc, "flash_user_exists"), "error")
            return render_template("auth/register.html", roles=USER_ROLES)

        user = User(email=email, password=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(flash_message(loc, "flash_register_ok"), "success")
        return redirect_for_role()

    return render_template("auth/register.html", roles=USER_ROLES)


@auth_bp.route("/logout")
@login_required
def logout():
    loc = normalize_locale(request.cookies.get("av_lang"))
    logout_user()
    flash(flash_message(loc, "flash_logout"), "success")
    return redirect(url_for("auth.login"))
