import re
import secrets

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from .. import db
from ..models.password_reset_token import PasswordResetToken
from ..models.user import User
from ..utils.email_utils import send_password_reset_email

auth_bp = Blueprint("auth", __name__)

PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$")


def _validate_password_complexity(password: str) -> bool:
    return bool(PASSWORD_REGEX.match(password))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not user.verify_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        if user.role not in {"student", "instructor"}:
            flash("Invalid user role.", "danger")
            return render_template("auth/login.html", email=email)

        session["user_id"] = user.id
        session["user_role"] = user.role
        flash("Logged in successfully.", "success")
        return redirect(url_for("exam.list_exams"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token_value = secrets.token_urlsafe(32)
            token_entry = PasswordResetToken.create_for_user(user.id, token_value)
            db.session.add(token_entry)
            db.session.commit()

            token_url = url_for("auth.reset_with_token", token=token_value, _external=True)
            send_password_reset_email(user, token_url)

        flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.reset_request"))

    return render_template("auth/reset_request.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_with_token(token: str):
    token_entry = PasswordResetToken.query.filter_by(token=token).first()

    if not token_entry or token_entry.used or token_entry.is_expired():
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.reset_request"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/reset_token.html", token=token)

        if not _validate_password_complexity(password):
            flash(
                "Password must be at least 8 characters with an uppercase letter, a number, and a special character.",
                "danger",
            )
            return render_template("auth/reset_token.html", token=token)

        token_entry.user.password_hash = generate_password_hash(password)
        token_entry.used = True
        db.session.commit()

        flash("Password updated successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_token.html", token=token)
