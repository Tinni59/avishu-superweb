from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from models import Order
from order_events import emit_order_created
from order_status import ORDER_TYPES, validate_new_order
from routes.helpers import role_required

client_bp = Blueprint("client", __name__, url_prefix="/client")


def _parse_deadline_form(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None


@client_bp.route("/")
@login_required
@role_required("client")
def dashboard():
    return render_template("client/dashboard.html")


@client_bp.route("/products")
@login_required
@role_required("client")
def products():
    return render_template("client/products.html")


@client_bp.route("/orders")
@login_required
@role_required("client")
def orders():
    order_list = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template(
        "client/orders.html",
        orders=order_list,
        order_types=ORDER_TYPES,
    )


@client_bp.route("/orders", methods=["POST"])
@login_required
@role_required("client")
def create_order():
    product_name = request.form.get("product_name", "").strip()
    order_type = request.form.get("type", "").strip()
    deadline = _parse_deadline_form(request.form.get("deadline", ""))

    ok, err = validate_new_order(order_type, deadline)
    if not ok:
        flash(err, "error")
        return redirect(url_for("client.orders"))

    if not product_name:
        flash("Укажите название продукта.", "error")
        return redirect(url_for("client.orders"))

    order = Order(
        user_id=current_user.id,
        product_name=product_name,
        type=order_type,
        status="created",
        deadline=deadline,
    )
    db.session.add(order)
    db.session.commit()

    emit_order_created(order, current_user.role)

    flash("Заказ создан.", "success")
    return redirect(url_for("client.orders"))
