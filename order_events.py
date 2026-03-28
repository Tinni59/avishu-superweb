"""Socket.IO: order_created / order_updated (WebSocket only, без polling)."""

from typing import Optional

from extensions import db, socketio
from models import User


def _order_dict(order):
    data = order.to_dict()
    user = getattr(order, "user", None)
    if user is None and order.user_id:
        user = db.session.get(User, order.user_id)
    data["client_email"] = user.email if user else None
    return data


def emit_order_created(order, actor_role: str):
    payload = {
        "message": "New client order created",
        "order": _order_dict(order),
        "actor_role": actor_role,
    }
    socketio.emit("order_created", payload, room=f"user:{order.user_id}")
    socketio.emit("order_created", payload, room="role:franchisee")
    socketio.emit("order_created", payload, room="role:production")


def emit_order_updated(order, actor_role: str, previous_status: Optional[str] = None):
    base = {
        "message": "Order updated",
        "order": _order_dict(order),
        "actor_role": actor_role,
        "previous_status": previous_status,
    }
    socketio.emit("order_updated", base, room=f"user:{order.user_id}")
    socketio.emit("order_updated", base, room="role:franchisee")
    socketio.emit("order_updated", base, room="role:production")
