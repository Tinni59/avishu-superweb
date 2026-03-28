from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Order
from order_events import emit_order_updated
from order_status import is_valid_franchisee_transition, next_statuses_for_franchisee
from routes.helpers import role_required

franchisee_bp = Blueprint("franchisee", __name__, url_prefix="/franchisee")


def _period_start(period: str) -> datetime:
    now = datetime.utcnow()
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # week (default)
    return now - timedelta(days=7)


@franchisee_bp.route("/")
@login_required
@role_required("franchisee")
def dashboard():
    period = request.args.get("period", "week")
    if period not in ("today", "week", "month"):
        period = "week"

    start = _period_start(period)
    orders_in_period = Order.query.filter(Order.created_at >= start).all()
    counts = {"created": 0, "accepted": 0, "in_production": 0, "done": 0}
    for o in orders_in_period:
        if o.status in counts:
            counts[o.status] += 1

    return render_template(
        "franchisee/dashboard.html",
        order_counts=counts,
        revenue_stub="—",
        plan_stub="72%",
        stats_period=period,
    )


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
