from online_exam.models.user import User


def test_valid_login_redirects_to_student_dashboard(client, sample_student):
    """Test that valid student login redirects to student dashboard."""
    response = client.post(
        "/login",
        data={"email": "student@example.com", "password": "Password123!"},
        follow_redirects=True,
    )

    assert response.request.path == "/student/dashboard"
    assert response.status_code == 200
    assert b"Student Dashboard" in response.data or b"Available Exams" in response.data


def test_valid_instructor_login_redirects_to_exams(client, sample_instructor):
    """Test that valid instructor login redirects to exams list."""
    response = client.post(
        "/login",
        data={"email": "instructor@example.com", "password": "Password123!"},
        follow_redirects=True,
    )

    assert response.request.path == "/exams"
    assert response.status_code == 200


def test_invalid_login_shows_error(client, sample_student):
    response = client.post(
        "/login",
        data={"email": "student@example.com", "password": "wrong"},
        follow_redirects=True,
    )

    assert b"Invalid email or password" in response.data


def test_password_is_hashed(app, sample_student):
    with app.app_context():
        user = User.query.filter_by(email="student@example.com").first()
        assert user is not None
        assert user.password_hash != "Password123!"
        assert user.verify_password("Password123!")
