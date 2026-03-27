from datetime import datetime

from flask_login import UserMixin

from extensions import db
from order_status import ORDER_STATUSES, ORDER_TYPES


USER_ROLES = ("client", "franchisee", "production")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, index=True)
    orders = db.relationship("Order", backref="user", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    product_name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="created", index=True)
    deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_name": self.product_name,
            "type": self.type,
            "status": self.status,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Order #{self.id} {self.product_name}>"
