from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db, socketio
from models import ORDER_TYPES, Order
from routes.helpers import role_required

client_bp = Blueprint("client", __name__, url_prefix="/client")


@client_bp.route("/")
@login_required
@role_required("client")
def dashboard():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("client/dashboard.html", orders=orders, order_types=ORDER_TYPES)


@client_bp.route("/orders", methods=["POST"])
@login_required
@role_required("client")
def create_order():
    product_name = request.form.get("product_name", "").strip()
    order_type = request.form.get("type", "").strip()
    deadline_raw = request.form.get("deadline", "").strip()

    if not product_name:
        flash("Укажите название продукта.", "error")
        return redirect(url_for("client.dashboard"))

    if order_type not in ORDER_TYPES:
        flash("Выберите корректный тип заказа.", "error")
        return redirect(url_for("client.dashboard"))

    deadline = None
    if deadline_raw:
        try:
            deadline = datetime.strptime(deadline_raw, "%Y-%m-%d")
        except ValueError:
            flash("Некорректный формат даты.", "error")
            return redirect(url_for("client.dashboard"))

    order = Order(
        user_id=current_user.id,
        product_name=product_name,
        type=order_type,
        status="created",
        deadline=deadline,
    )
    db.session.add(order)
    db.session.commit()

    payload = {
        "message": "New client order created",
        "order": order.to_dict(),
        "actor_role": current_user.role,
    }
    socketio.emit("order_created", payload, room="role:franchisee")
    socketio.emit("order_created", payload, room="role:production")

    flash("Заказ создан.", "success")
    return redirect(url_for("client.dashboard"))
