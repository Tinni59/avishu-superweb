from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from models import USER_ROLES, User
from routes.helpers import redirect_for_role

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Неверный email или пароль.", "error")
            return render_template("auth/login.html")

        login_user(user)
        flash("Вход выполнен успешно.", "success")
        return redirect_for_role()

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()

        if not email or not password or role not in USER_ROLES:
            flash("Заполните все поля и выберите корректную роль.", "error")
            return render_template("auth/register.html", roles=USER_ROLES)

        if User.query.filter_by(email=email).first():
            flash("Пользователь с таким email уже существует.", "error")
            return render_template("auth/register.html", roles=USER_ROLES)

        user = User(email=email, password=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Регистрация завершена.", "success")
        return redirect_for_role()

    return render_template("auth/register.html", roles=USER_ROLES)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for("auth.login"))
