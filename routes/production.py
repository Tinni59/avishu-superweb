from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db, socketio
from models import ORDER_STATUSES, Order
from routes.helpers import role_required


production_bp = Blueprint("production", __name__, url_prefix="/production")


@production_bp.route("/")
@login_required
@role_required("production")
def dashboard():
    active_orders = (
        Order.query.filter(Order.status.in_(("created", "accepted", "in_production")))
        .order_by(Order.created_at.desc())
        .all()
    )
    completed_orders = Order.query.filter_by(status="done").order_by(Order.created_at.desc()).all()
    return render_template(
        "production/dashboard.html",
        active_orders=active_orders,
        completed_orders=completed_orders,
        order_statuses=ORDER_STATUSES,
        current_user=current_user,
    )


@production_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@role_required("production")
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    next_status = request.form.get("status", "").strip()

    if next_status not in ORDER_STATUSES:
        flash("Недопустимый статус.", "error")
        return redirect(url_for("production.dashboard"))

    order.status = next_status
    db.session.commit()

    socketio.emit(
        "order_updated",
        {
            "message": "Order moved by production",
            "order": order.to_dict(),
            "actor_role": current_user.role,
        },
        room=f"user:{order.user_id}",
    )
    socketio.emit(
        "order_updated",
        {
            "message": "Production updated order status",
            "order": order.to_dict(),
            "actor_role": current_user.role,
        },
        room="role:franchisee",
    )
    socketio.emit(
        "order_updated",
        {
            "message": "Production updated order status",
            "order": order.to_dict(),
            "actor_role": current_user.role,
        },
        room="role:production",
    )

    flash("Статус заказа обновлен.", "success")
    return redirect(url_for("production.dashboard"))
