from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from i18n import flash_message, normalize_locale
from catalog import get_catalog
from extensions import db
from models import Order
from order_events import emit_order_created
from order_status import ORDER_TYPES, validate_new_order
from routes.helpers import role_required

client_bp = Blueprint("client", __name__, url_prefix="/client")


def _parse_deadline_form(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None


def _session_cart():
    cart = session.get("cart")
    if not isinstance(cart, list):
        cart = []
        session["cart"] = cart
    return cart


def _create_order_for_user(product_name: str, order_type: str, deadline):
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
    return order


@client_bp.route("/")
@login_required
@role_required("client")
def dashboard():
    return render_template("client/dashboard.html", catalog=get_catalog())


@client_bp.route("/products")
@login_required
@role_required("client")
def products():
    return redirect(url_for("client.dashboard"))


@client_bp.route("/orders")
@login_required
@role_required("client")
def orders():
    order_list = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    loyalty_pct = min(100, len(order_list) * 12 + 8)
    return render_template(
        "client/orders.html",
        orders=order_list,
        order_types=ORDER_TYPES,
        loyalty_pct=loyalty_pct,
    )


@client_bp.route("/cart", methods=["GET", "POST"])
@login_required
@role_required("client")
def cart():
    loc = normalize_locale(request.cookies.get("av_lang"))
    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        order_type = request.form.get("type", "").strip()
        deadline = _parse_deadline_form(request.form.get("deadline", ""))

        ok, err = validate_new_order(order_type, deadline, locale=loc)
        if not ok:
            flash(err, "error")
            return redirect(url_for("client.dashboard"))

        if not product_name:
            flash(flash_message(loc, "flash_product_missing"), "error")
            return redirect(url_for("client.dashboard"))

        cart = _session_cart()
        cart.append(
            {
                "product_name": product_name,
                "type": order_type,
                "deadline": deadline.isoformat() if deadline else None,
            }
        )
        session["cart"] = cart
        session.modified = True
        flash(flash_message(loc, "flash_cart_added"), "success")
        return redirect(url_for("client.dashboard"))

    return render_template("client/cart.html", cart=_session_cart())


@client_bp.route("/cart/checkout", methods=["POST"])
@login_required
@role_required("client")
def checkout_cart():
    loc = normalize_locale(request.cookies.get("av_lang"))
    cart = _session_cart()
    if not cart:
        flash(flash_message(loc, "flash_cart_empty"), "error")
        return redirect(url_for("client.cart"))

    for item in cart:
        order_type = item.get("type", "").strip()
        deadline = None
        if item.get("deadline"):
            try:
                deadline = datetime.fromisoformat(item["deadline"])
            except (ValueError, TypeError):
                deadline = None
        ok, err = validate_new_order(order_type, deadline, locale=loc)
        if not ok:
            flash(err, "error")
            return redirect(url_for("client.cart"))
        _create_order_for_user(item["product_name"], order_type, deadline)

    session["cart"] = []
    session.modified = True
    flash(flash_message(loc, "flash_checkout_ok"), "success")
    return redirect(url_for("client.orders"))


@client_bp.route("/orders", methods=["POST"])
@login_required
@role_required("client")
def create_order():
    loc = normalize_locale(request.cookies.get("av_lang"))
    product_name = request.form.get("product_name", "").strip()
    order_type = request.form.get("type", "").strip()
    deadline = _parse_deadline_form(request.form.get("deadline", ""))

    ok, err = validate_new_order(order_type, deadline, locale=loc)
    if not ok:
        flash(err, "error")
        return redirect(request.referrer or url_for("client.dashboard"))

    if not product_name:
        flash(flash_message(loc, "flash_product_name_required"), "error")
        return redirect(request.referrer or url_for("client.dashboard"))

    _create_order_for_user(product_name, order_type, deadline)

    flash(flash_message(loc, "flash_order_created"), "success")
    next_url = request.form.get("next") or url_for("client.orders")
    return redirect(next_url)
