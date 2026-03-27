"""Socket.IO уведомления о заказах (опционально; страницы работают и без realtime)."""

from extensions import socketio


def emit_order_created(order, actor_role: str):
    payload = {
        "message": "New client order created",
        "order": order.to_dict(),
        "actor_role": actor_role,
    }
    socketio.emit("order_created", payload, room="role:franchisee")
    socketio.emit("order_created", payload, room="role:production")


def emit_order_updated(order, actor_role: str):
    base = {
        "message": "Order updated",
        "order": order.to_dict(),
        "actor_role": actor_role,
    }
    socketio.emit("order_updated", base, room=f"user:{order.user_id}")
    socketio.emit("order_updated", base, room="role:franchisee")
    socketio.emit("order_updated", base, room="role:production")
