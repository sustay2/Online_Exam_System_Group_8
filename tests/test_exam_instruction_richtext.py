import pytest

from online_exam import create_app, db
from online_exam.models import Exam


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SERVER_NAME": "localhost",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for tests
    }

    app = create_app(test_config)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


def test_create_exam_with_rich_instructions(client):
    instructions = "<b>Bold</b>"

    response = client.post(
        "/exams/create",
        data={"title": "Test Exam", "instructions": instructions},
        follow_redirects=True,
    )

    assert response.status_code == 200

    exam = Exam.query.filter_by(title="Test Exam").first()
    assert exam.instructions == instructions
