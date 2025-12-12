from functools import wraps
from typing import Callable

from flask import redirect, session, url_for


def login_required(view_func: Callable):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(*roles: str):
    def decorator(view_func: Callable):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("auth.login"))

            user_role = session.get("user_role")
            if user_role not in roles:
                return "Forbidden", 403

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
