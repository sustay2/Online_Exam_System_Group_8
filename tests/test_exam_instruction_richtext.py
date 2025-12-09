import pytest

from online_exam import create_app, db
from online_exam.models import Exam, User


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


@pytest.fixture
def instructor(app):
    """Create a test instructor user with all required fields."""
    user = User(
        username="instructor1",  # Required
        name="Test Instructor",  # Required
        email="instructor@example.com",
        role="instructor",
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def logged_in_client(client, instructor):
    """Log in the instructor in the test client session."""
    with client.session_transaction() as sess:
        sess["user_id"] = instructor.id  # match your login session key
        sess["role"] = instructor.role  # optional, if your app uses role
    return client


def test_create_exam_with_rich_instructions(logged_in_client):
    """Test creating an exam with rich-text instructions."""
    client = logged_in_client

    # Create exam with rich-text instructions
    instructions = "<b>Bold text</b>\n<ul><li>Item 1</li><li>Item 2</li></ul>\n<a href='https://example.com'>Link</a>"
    response = client.post(
        "/exams/create",  # Make sure the URL matches your blueprint
        data={"title": "Test Exam", "instructions": instructions},
        follow_redirects=True,
    )
    assert response.status_code == 200

    exam = Exam.query.filter_by(title="Test Exam").first()
    assert exam is not None
    assert exam.instructions == instructions
