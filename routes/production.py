from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from i18n import flash_message, normalize_locale
from extensions import db
from models import Order
from order_events import emit_order_updated
from order_status import is_valid_production_transition
from routes.helpers import role_required

production_bp = Blueprint("production", __name__, url_prefix="/production")


@production_bp.route("/")
@login_required
@role_required("production")
def dashboard():
    counts = {
        "requested": Order.query.filter_by(status="accepted").count(),
        "in_progress": Order.query.filter_by(status="in_production").count(),
        "completed": Order.query.filter_by(status="done").count(),
    }
    return render_template("production/dashboard.html", stats=counts)


@production_bp.route("/orders")
@login_required
@role_required("production")
def orders():
    visible = (
        Order.query.filter(Order.status.in_(("accepted", "in_production")))
        .order_by(Order.created_at.desc())
        .all()
    )
    done_list = Order.query.filter_by(status="done").order_by(Order.created_at.desc()).all()
    return render_template(
        "production/orders.html",
        visible_orders=visible,
        completed_orders=done_list,
    )


@production_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@role_required("production")
def update_status(order_id):
    loc = normalize_locale(request.cookies.get("av_lang"))
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "").strip()

    if order.status not in ("accepted", "in_production"):
        flash(flash_message(loc, "flash_prod_unavailable"), "error")
        return redirect(url_for("production.orders"))

    if not is_valid_production_transition(order.status, new_status):
        flash(
            flash_message(
                loc,
                "flash_transition_error",
                current=order.status,
                new=new_status,
            ),
            "error",
        )
        return redirect(url_for("production.orders"))

    previous_status = order.status
    order.status = new_status
    db.session.commit()
    emit_order_updated(order, current_user.role, previous_status=previous_status)
    flash(flash_message(loc, "flash_status_updated"), "success")
    return redirect(url_for("production.orders"))
