from flask import Flask, redirect, url_for
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
        PasswordResetToken,
        Question,
        Submission,
        User,
    )

    migrate.init_app(app, db)

    # Register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.exam_routes import exam_bp
    from .routes.grading_routes import grading_bp
    from .routes.question_routes import question_bp
    from .routes.student_routes import student_bp
    from .routes.schedule_routes import schedule_bp
    from .routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(analytics_bp)

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    return app
