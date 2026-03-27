from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from models import Order
from order_events import emit_order_updated
from order_status import is_valid_franchisee_transition, next_statuses_for_franchisee
from routes.helpers import role_required

franchisee_bp = Blueprint("franchisee", __name__, url_prefix="/franchisee")


@franchisee_bp.route("/")
@login_required
@role_required("franchisee")
def dashboard():
    return render_template("franchisee/dashboard.html")


@franchisee_bp.route("/orders")
@login_required
@role_required("franchisee")
def orders():
    order_list = Order.query.order_by(Order.created_at.desc()).all()
    return render_template(
        "franchisee/orders.html",
        orders=order_list,
        next_statuses_for_franchisee=next_statuses_for_franchisee,
    )


@franchisee_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@role_required("franchisee")
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "").strip()

    if not is_valid_franchisee_transition(order.status, new_status):
        flash(
            f"Переход из «{order.status}» в «{new_status}» недопустим.",
            "error",
        )
        return redirect(url_for("franchisee.orders"))

    order.status = new_status
    db.session.commit()
    emit_order_updated(order, current_user.role)
    flash("Статус заказа обновлён.", "success")
    return redirect(url_for("franchisee.orders"))
