"""Переключение светлой/тёмной темы (cookie)."""

from flask import Blueprint, redirect, request, url_for

theme_bp = Blueprint("theme", __name__)


@theme_bp.route("/theme/set/<mode>")
def set_theme(mode):
    if mode not in ("light", "dark"):
        return redirect(url_for("auth.login"))
    dest = request.referrer or url_for("auth.login")
    resp = redirect(dest)
    resp.set_cookie(
        "av_theme",
        mode,
        max_age=60 * 60 * 24 * 365,
        samesite="Lax",
        path="/",
    )
    return resp
