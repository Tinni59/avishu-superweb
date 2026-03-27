from functools import wraps

from flask import abort, redirect, url_for
from flask_login import current_user


ROLE_ENDPOINTS = {
    "client": "client.dashboard",
    "franchisee": "franchisee.dashboard",
    "production": "production.dashboard",
}


def redirect_for_role():
    endpoint = ROLE_ENDPOINTS.get(getattr(current_user, "role", None))
    if not endpoint:
        abort(403)
    return redirect(url_for(endpoint))


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role != role:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
