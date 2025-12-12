from flask import Flask, g, redirect, request, session, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from .config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__)

    # Load config
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)

    from .models import (  # noqa: F401
        Answer,
        Exam,
        LoginAttempt,
        PasswordResetToken,
        Question,
        Submission,
        User,
    )

    migrate.init_app(app, db)

    # Register blueprints
    from .routes.analytics_routes import analytics_bp
    from .routes.auth_routes import auth_bp
    from .routes.exam_routes import exam_bp
    from .routes.grading_routes import grading_bp
    from .routes.question_routes import question_bp
    from .routes.schedule_routes import schedule_bp
    from .routes.student_routes import student_bp
    from .routes.rbac_routes import rbac_bp
    from .routes.profile_routes import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(rbac_bp)
    app.register_blueprint(profile_bp)

    auth_paths = {"/login", "/register", "/auth/verify-otp"}

    @app.before_request
    def load_current_user():
        user_id = session.get("user_id")
        g.current_user = User.query.get(user_id) if user_id else None

    def _is_public_path(path: str) -> bool:
        if path.startswith("/static/") or path == "/favicon.ico":
            return True

        if path == "/":
            return True

        if path in auth_paths or path.startswith("/reset-password"):
            return True

        return False

    @app.before_request
    def enforce_rbac():
        path = request.path

        if _is_public_path(path):
            return None

        user_id = session.get("user_id")
        user_role = session.get("user_role")

        if not user_id or not user_role:
            return redirect(url_for("auth.login"))

        profile_paths = {"/profile", "/profile/2fa/enable", "/profile/2fa/disable"}

        if path.startswith("/student"):
            if user_role != "student":
                return "Forbidden", 403
            return None

        if path in profile_paths:
            return None

        if user_role == "student":
            return "Forbidden", 403

    @app.context_processor
    def inject_user():
        current_user = getattr(g, "current_user", None)
        return {
            "current_user": current_user,
            "is_authenticated": current_user is not None,
        }

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    return app
