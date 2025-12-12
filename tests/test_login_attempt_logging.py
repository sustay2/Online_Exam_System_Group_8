from datetime import datetime, timedelta

import pytest

from online_exam.models.login_attempt import LoginAttempt


pytestmark = pytest.mark.rbac_role("none")


def test_failed_login_is_logged(client, sample_student, app):
    response = client.post(
        "/login",
        data={"email": "student@example.com", "password": "wrong"},
        environ_base={"REMOTE_ADDR": "10.0.0.1"},
    )

    assert response.status_code == 200

    with app.app_context():
        attempts = LoginAttempt.query.all()
        assert len(attempts) == 1
        attempt = attempts[0]
        assert attempt.success is False
        assert attempt.user_identifier == "student@example.com"
        assert attempt.ip_address == "10.0.0.1"
        assert attempt.timestamp is not None
        assert attempt.timestamp <= datetime.utcnow()


def test_successful_login_is_logged(client, sample_instructor, app):
    response = client.post(
        "/login",
        data={"email": "instructor@example.com", "password": "Password123!"},
        headers={"X-Forwarded-For": "203.0.113.5, 70.0.0.1"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        attempts = LoginAttempt.query.order_by(LoginAttempt.id.desc()).all()
        assert attempts
        attempt = attempts[0]
        assert attempt.success is True
        assert attempt.user_identifier == "instructor@example.com"
        assert attempt.ip_address == "203.0.113.5"
        assert attempt.timestamp >= datetime.utcnow() - timedelta(minutes=5)


def test_logging_does_not_block_login_flow(client, sample_student, app):
    response = client.post(
        "/login",
        data={"email": "student@example.com", "password": "Password123!"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.request.path == "/student/dashboard"

    with app.app_context():
        attempt = LoginAttempt.query.order_by(LoginAttempt.id.desc()).first()
        assert attempt is not None
        assert attempt.success is True
