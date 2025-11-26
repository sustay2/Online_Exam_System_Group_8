from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # register routes
    from .routes.auth_routes import auth_bp
    from .routes.exam_routes import exam_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(exam_bp)

    @app.route("/")
    def home():
        return "Hello, Exam System!"

    return app