"""Переключение языка интерфейса (cookie)."""

from flask import Blueprint, redirect, request, url_for

from i18n import SUPPORTED_LOCALES

locale_bp = Blueprint("locale", __name__)


@locale_bp.route("/locale/set/<code>")
def set_locale(code):
    if code not in SUPPORTED_LOCALES:
        return redirect(request.referrer or url_for("auth.login"))
    dest = request.referrer or url_for("auth.login")
    resp = redirect(dest)
    resp.set_cookie(
        "av_lang",
        code,
        max_age=60 * 60 * 24 * 365,
        samesite="Lax",
        path="/",
    )
    return resp
