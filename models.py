import json
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


class CatalogProduct(db.Model):
    """Товары витрины (опционально; иначе каталог строится из static/images/catalog)."""

    __tablename__ = "catalog_product"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    line = db.Column(db.String(128), nullable=False, default="Коллекция")
    product_type = db.Column(db.String(32), nullable=False, default="in_stock")
    price = db.Column(db.String(64), nullable=False, default="—")
    detail = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    images_json = db.Column(db.Text, nullable=False, default="[]")

    def to_catalog_dict(self):
        try:
            images = json.loads(self.images_json or "[]")
        except (json.JSONDecodeError, TypeError):
            images = []
        return {
            "id": self.slug,
            "name": self.name,
            "line": self.line,
            "type": self.product_type,
            "price": self.price,
            "detail": self.detail or "",
            "images": images,
        }

    def __repr__(self):
        return f"<CatalogProduct {self.name}>"
