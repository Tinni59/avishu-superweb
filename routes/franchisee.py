from flask import Blueprint, render_template
from flask_login import login_required

from models import Order
from routes.helpers import role_required


franchisee_bp = Blueprint("franchisee", __name__, url_prefix="/franchisee")


@franchisee_bp.route("/")
@login_required
@role_required("franchisee")
def dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("franchisee/dashboard.html", orders=orders)
