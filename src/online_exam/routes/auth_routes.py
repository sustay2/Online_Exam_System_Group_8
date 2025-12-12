import re
import secrets
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from .. import db
from ..models.login_attempt import LoginAttempt
from ..models.password_reset_token import PasswordResetToken
from ..models.user import User
from ..utils.email_utils import send_otp_email, send_password_reset_email
from ..utils.otp_utils import generate_otp_code, hash_otp, otp_expiry_time

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

        def _get_client_ip() -> str:
            forwarded_for = request.headers.get("X-Forwarded-For", "")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()

            return request.remote_addr or "unknown"

        def _log_attempt(success: bool) -> None:
            attempt = LoginAttempt(
                user_identifier=email,
                ip_address=_get_client_ip(),
                success=success,
            )
            db.session.add(attempt)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        if not user or not user.verify_password(password):
            flash("Invalid email or password.", "danger")
            _log_attempt(False)
            return render_template("auth/login.html", email=email)

        if user.role not in {"student", "instructor", "admin"}:
            flash("Invalid user role.", "danger")
            _log_attempt(False)
            return render_template("auth/login.html", email=email, show_header=False)

        if user.two_factor_enabled:
            otp_code = generate_otp_code()
            user.otp_code = hash_otp(otp_code)
            user.otp_expires_at = otp_expiry_time()
            db.session.add(user)
            db.session.commit()

            send_otp_email(user, otp_code)
            session.clear()
            session["pending_2fa_user_id"] = user.id
            session["pending_2fa_email"] = email
            flash("A verification code has been sent to your email.", "info")
            return redirect(url_for("auth.verify_otp"))

        session["user_id"] = user.id
        session["user_role"] = user.role
        flash(f"Welcome back, {user.name}!", "success")

        _log_attempt(True)

        # ROLE-BASED REDIRECT
        if user.role == "student":
            return redirect(url_for("student.dashboard"))

        # admin
        if user.role == "admin":
            return redirect(url_for("analytics.login_attempts"))

        # instructor
        return redirect(url_for("exam.list_exams"))

    return render_template("auth/login.html")


@auth_bp.route("/auth/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending_user_id = session.get("pending_2fa_user_id")

    if not pending_user_id:
        return redirect(url_for("auth.login"))

    user = User.query.get(pending_user_id)

    if not user or not user.two_factor_enabled:
        session.pop("pending_2fa_user_id", None)
        session.pop("pending_2fa_email", None)
        return redirect(url_for("auth.login"))

    def _get_client_ip() -> str:
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.remote_addr or "unknown"

    def _log_attempt(success: bool) -> None:
        attempt = LoginAttempt(
            user_identifier=session.get("pending_2fa_email", user.email),
            ip_address=_get_client_ip(),
            success=success,
        )
        db.session.add(attempt)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    if request.method == "POST":
        submitted_code = request.form.get("otp", "").strip()

        if not submitted_code:
            flash("Please enter the verification code.", "warning")
            return render_template("auth/verify_otp.html", show_header=False)

        if not user.otp_code or not user.otp_expires_at:
            flash("Verification code not found. Please log in again.", "danger")
            session.pop("pending_2fa_user_id", None)
            session.pop("pending_2fa_email", None)
            return redirect(url_for("auth.login"))

        if datetime.utcnow() > user.otp_expires_at:
            flash("Your verification code has expired. Please log in again.", "danger")
            user.otp_code = None
            user.otp_expires_at = None
            db.session.commit()
            session.pop("pending_2fa_user_id", None)
            session.pop("pending_2fa_email", None)
            _log_attempt(False)
            return redirect(url_for("auth.login"))

        if not user.otp_is_valid(submitted_code):
            flash("Invalid verification code.", "danger")
            _log_attempt(False)
            return render_template("auth/verify_otp.html", show_header=False)

        user.otp_code = None
        user.otp_expires_at = None
        db.session.commit()
        session.pop("pending_2fa_user_id", None)
        session.pop("pending_2fa_email", None)
        session["user_id"] = user.id
        session["user_role"] = user.role
        flash("Two-factor verification successful.", "success")
        _log_attempt(True)

        if user.role == "student":
            return redirect(url_for("student.dashboard"))
        if user.role == "admin":
            return redirect(url_for("analytics.login_attempts"))
        return redirect(url_for("exam.list_exams"))

    return render_template("auth/verify_otp.html", show_header=False)


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


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "student").strip().lower()

        if not all([name, email, password, confirm_password]):
            flash("All fields are required.", "danger")
            return render_template("auth/register.html", name=name, email=email, role=role)

        if role not in {"student", "instructor"}:
            flash("Invalid role selected.", "danger")
            return render_template("auth/register.html", name=name, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html", name=name, email=email, role=role)

        if not _validate_password_complexity(password):
            flash(
                "Password must be at least 8 characters with an uppercase letter, a number, and a special character.",
                "danger",
            )
            return render_template("auth/register.html", name=name, email=email, role=role)

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return render_template("auth/register.html", name=name, email=email, role=role)

        new_user = User(username=email, name=name, email=email, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")
