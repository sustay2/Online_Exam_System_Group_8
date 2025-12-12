from flask import Blueprint, flash, redirect, render_template, session, url_for

from .. import db
from ..models.user import User
from ..utils.auth import login_required

profile_bp = Blueprint("profile", __name__)


def _current_user():
    user_id = session.get("user_id")
    return User.query.get(user_id) if user_id else None


@profile_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    user = _current_user()
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    return render_template("profile.html", user=user)


@profile_bp.route("/profile/2fa/enable", methods=["POST"])
@login_required
def enable_two_factor():
    user = _current_user()
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    user.two_factor_enabled = True
    user.otp_code = None
    user.otp_expires_at = None
    db.session.commit()
    flash(
        "Two-factor authentication enabled. You will be asked for a code on next login.", "success"
    )
    return redirect(url_for("profile.profile"))


@profile_bp.route("/profile/2fa/disable", methods=["POST"])
@login_required
def disable_two_factor():
    user = _current_user()
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    user.two_factor_enabled = False
    user.otp_code = None
    user.otp_expires_at = None
    db.session.commit()
    flash("Two-factor authentication disabled.", "info")
    return redirect(url_for("profile.profile"))
