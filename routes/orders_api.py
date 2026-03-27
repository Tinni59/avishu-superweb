"""JSON API для заказов: POST/GET /orders, GET/PATCH /orders/<id>."""

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from extensions import db
from models import Order
from order_events import emit_order_created, emit_order_updated
from order_status import (
    ORDER_STATUSES,
    is_valid_franchisee_transition,
    is_valid_production_transition,
    validate_new_order,
)
orders_api_bp = Blueprint("orders_api", __name__)


def _parse_deadline(raw):
    if raw is None or raw == "":
        return None
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw.replace("Z", ""), fmt)
            except ValueError:
                continue
    return None


@orders_api_bp.route("/orders", methods=["GET", "POST"])
@login_required
def orders_collection():
    if request.method == "GET":
        if current_user.role == "client":
            items = (
                Order.query.filter_by(user_id=current_user.id)
                .order_by(Order.created_at.desc())
                .all()
            )
        elif current_user.role == "franchisee":
            items = Order.query.order_by(Order.created_at.desc()).all()
        elif current_user.role == "production":
            items = (
                Order.query.filter(Order.status.in_(("accepted", "in_production")))
                .order_by(Order.created_at.desc())
                .all()
            )
        else:
            return jsonify({"error": "Доступ запрещён."}), 403
        return jsonify({"orders": [o.to_dict() for o in items]})

    # POST — только клиент
    if current_user.role != "client":
        return jsonify({"error": "Создавать заказы может только клиент."}), 403

    data = request.get_json(silent=True) or {}
    product_name = (data.get("product_name") or "").strip()
    order_type = (data.get("type") or "").strip()
    deadline = _parse_deadline(data.get("deadline"))

    ok, err = validate_new_order(order_type, deadline)
    if not ok:
        return jsonify({"error": err}), 400

    if not product_name:
        return jsonify({"error": "Укажите название продукта."}), 400

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
    return jsonify({"order": order.to_dict()}), 201


@orders_api_bp.route("/orders/<int:order_id>", methods=["GET", "PATCH"])
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    if request.method == "GET":
        if current_user.role == "client":
            if order.user_id != current_user.id:
                return jsonify({"error": "Заказ не найден."}), 404
        elif current_user.role == "franchisee":
            pass
        elif current_user.role == "production":
            if order.status not in ("accepted", "in_production"):
                return jsonify({"error": "Заказ недоступен."}), 404
        else:
            return jsonify({"error": "Доступ запрещён."}), 403
        return jsonify({"order": order.to_dict()})

    # PATCH
    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip()

    if not new_status:
        return jsonify({"error": "Укажите status."}), 400
    if new_status not in ORDER_STATUSES:
        return jsonify({"error": "Недопустимый статус."}), 400

    if current_user.role == "franchisee":
        if not is_valid_franchisee_transition(order.status, new_status):
            return jsonify(
                {
                    "error": (
                        f"Переход из «{order.status}» в «{new_status}» "
                        "недопустим для франчайзи."
                    ),
                }
            ), 400
    elif current_user.role == "production":
        if not is_valid_production_transition(order.status, new_status):
            return jsonify(
                {
                    "error": (
                        f"Переход из «{order.status}» в «{new_status}» "
                        "недопустим для производства."
                    ),
                }
            ), 400
    else:
        return jsonify({"error": "Изменение статуса недоступно."}), 403

    order.status = new_status
    db.session.commit()
    emit_order_updated(order, current_user.role)
    return jsonify({"order": order.to_dict()})
