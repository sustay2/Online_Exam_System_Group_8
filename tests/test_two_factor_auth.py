import pytest
from datetime import datetime, timedelta

from online_exam import db
from online_exam.models.user import User

pytestmark = pytest.mark.rbac_role("none")


def _enable_2fa(user: User):
    user.two_factor_enabled = True
    user.otp_code = None
    user.otp_expires_at = None
    db.session.commit()


def test_login_without_two_factor(client, sample_instructor):
    response = client.post(
        "/login",
        data={"email": sample_instructor.email, "password": "Password123!"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/exams" in response.headers.get("Location", "")


def test_login_redirects_to_otp_when_enabled(client, sample_instructor, monkeypatch):
    _enable_2fa(sample_instructor)
    monkeypatch.setattr("online_exam.routes.auth_routes.generate_otp_code", lambda: "123456")

    response = client.post(
        "/login",
        data={"email": sample_instructor.email, "password": "Password123!"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/auth/verify-otp" in response.headers.get("Location", "")
    with client.session_transaction() as session:
        assert session.get("user_id") is None
        assert session.get("pending_2fa_user_id") == sample_instructor.id


def test_correct_otp_completes_login(client, sample_instructor, app, monkeypatch):
    _enable_2fa(sample_instructor)
    monkeypatch.setattr("online_exam.routes.auth_routes.generate_otp_code", lambda: "654321")

    client.post(
        "/login",
        data={"email": sample_instructor.email, "password": "Password123!"},
    )

    verify_response = client.post(
        "/auth/verify-otp", data={"otp": "654321"}, follow_redirects=False
    )

    assert verify_response.status_code == 302
    assert "/exams" in verify_response.headers.get("Location", "")
    with client.session_transaction() as session:
        assert session.get("user_id") == sample_instructor.id
        assert session.get("pending_2fa_user_id") is None

    with app.app_context():
        refreshed = db.session.get(User, sample_instructor.id)
        assert refreshed.otp_code is None
        assert refreshed.otp_expires_at is None


def test_incorrect_otp_rejected(client, sample_instructor, monkeypatch):
    _enable_2fa(sample_instructor)
    monkeypatch.setattr("online_exam.routes.auth_routes.generate_otp_code", lambda: "222222")

    client.post(
        "/login",
        data={"email": sample_instructor.email, "password": "Password123!"},
    )

    verify_response = client.post("/auth/verify-otp", data={"otp": "000000"}, follow_redirects=True)

    assert verify_response.status_code == 200
    assert b"Invalid verification code" in verify_response.data
    with client.session_transaction() as session:
        assert session.get("user_id") is None
        assert session.get("pending_2fa_user_id") == sample_instructor.id


def test_expired_otp_rejected(client, sample_instructor, app, monkeypatch):
    _enable_2fa(sample_instructor)
    monkeypatch.setattr("online_exam.routes.auth_routes.generate_otp_code", lambda: "333333")

    client.post(
        "/login",
        data={"email": sample_instructor.email, "password": "Password123!"},
    )

    with app.app_context():
        user = db.session.get(User, sample_instructor.id)
        user.otp_expires_at = datetime.utcnow() - timedelta(minutes=10)
        db.session.commit()

    verify_response = client.post(
        "/auth/verify-otp", data={"otp": "333333"}, follow_redirects=False
    )

    assert verify_response.status_code == 302
    assert "/login" in verify_response.headers.get("Location", "")
    with client.session_transaction() as session:
        assert session.get("pending_2fa_user_id") is None


def test_otp_cannot_be_reused(client, sample_instructor, app, monkeypatch):
    _enable_2fa(sample_instructor)
    monkeypatch.setattr("online_exam.routes.auth_routes.generate_otp_code", lambda: "999999")

    client.post(
        "/login",
        data={"email": sample_instructor.email, "password": "Password123!"},
    )

    client.post("/auth/verify-otp", data={"otp": "999999"})

    second_attempt = client.post("/auth/verify-otp", data={"otp": "999999"}, follow_redirects=False)

    assert second_attempt.status_code == 302
    assert "/login" in second_attempt.headers.get("Location", "")
    with app.app_context():
        user = db.session.get(User, sample_instructor.id)
        assert user.otp_code is None
        assert user.two_factor_enabled is True
