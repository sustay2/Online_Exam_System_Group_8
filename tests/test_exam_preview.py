import os
import sys
from datetime import datetime

import pytest

# Add src folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from online_exam import create_app, db
from online_exam.models.exam import Exam


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )

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
def sample_exam(app):
    """Create a sample exam with instructions."""
    exam = Exam(
        title="Sample Exam",
        description="This is a sample exam for testing.",
        instructions="<b>Answer all questions carefully.</b>",
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(exam)
    db.session.commit()
    return exam


def test_exam_preview_page(client, sample_exam):
    """Test viewing an exam preview shows title, description, and instructions."""
    url = f"/exams/{sample_exam.id}"
    response = client.get(url)
    html = response.data.decode()

    assert response.status_code == 200
    assert sample_exam.title in html
    assert sample_exam.description in html
    # Ensure instructions HTML is rendered safely
    assert "Answer all questions carefully." in html
    # Check for the 'Edit Exam' button because status is draft
    assert "Edit Exam" in html
    # Check for 'Publish Exam' button
    assert "Publish Exam" in html


def test_exam_preview_published_buttons(client, sample_exam, app):
    """Test preview page for published exam disables edit."""
    with app.app_context():
        sample_exam.status = "published"
        db.session.commit()

    url = f"/exams/{sample_exam.id}"
    response = client.get(url)
    html = response.data.decode()

    assert response.status_code == 200
    # Edit Exam button should not appear for published exam
    assert "Edit Exam" not in html
    # Published label should be present
    assert "Published" in html
