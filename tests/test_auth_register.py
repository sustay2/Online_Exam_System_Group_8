import pytest

from online_exam.models.user import User


pytestmark = pytest.mark.rbac_role("none")


@pytest.fixture
def registration_data():
    return {
        "name": "Test User",
        "email": "newuser@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "student",
    }


def test_valid_registration(client, app, registration_data):
    response = client.post("/register", data=registration_data, follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with app.app_context():
        user = User.query.filter_by(email=registration_data["email"]).first()
        assert user is not None
        assert user.name == registration_data["name"]
        assert user.role == "student"
        assert user.password_hash != registration_data["password"]
        assert user.verify_password(registration_data["password"])


def test_duplicate_email_registration(client, app, registration_data):
    client.post("/register", data=registration_data)
    duplicate_response = client.post("/register", data=registration_data, follow_redirects=True)

    assert b"Email is already registered." in duplicate_response.data

    with app.app_context():
        assert User.query.filter_by(email=registration_data["email"]).count() == 1


def test_password_complexity_failure(client, app):
    weak_data = {
        "name": "Weak User",
        "email": "weak@example.com",
        "password": "abc123",
        "confirm_password": "abc123",
        "role": "student",
    }

    weak_response = client.post("/register", data=weak_data, follow_redirects=True)
    assert b"Password must be at least 8 characters" in weak_response.data

    with app.app_context():
        assert User.query.filter_by(email=weak_data["email"]).count() == 0

    strong_data = {
        "name": "Strong User",
        "email": "strong@example.com",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "role": "student",
    }

    strong_response = client.post("/register", data=strong_data, follow_redirects=False)
    assert strong_response.status_code == 302


def test_missing_fields(client):
    response = client.post(
        "/register",
        data={"name": "", "email": "", "password": "", "confirm_password": "", "role": "student"},
        follow_redirects=True,
    )

    assert b"All fields are required." in response.data


def test_role_selection(client, app):
    instructor_data = {
        "name": "Instructor User",
        "email": "instructor2@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "instructor",
    }

    response = client.post("/register", data=instructor_data, follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        user = User.query.filter_by(email=instructor_data["email"]).first()
        assert user is not None
        assert user.role == "instructor"
