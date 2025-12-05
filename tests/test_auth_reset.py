from datetime import datetime, timedelta

from online_exam import db
from online_exam.models.password_reset_token import PasswordResetToken


def test_reset_request_creates_token(client, app, sample_student):
    response = client.post(
        "/reset-password", data={"email": "student@example.com"}, follow_redirects=True
    )
    assert b"reset link has been sent" in response.data

    with app.app_context():
        tokens = PasswordResetToken.query.all()
        assert len(tokens) == 1
        assert tokens[0].user_id == sample_student.id


def test_reset_flow_updates_password(client, app, sample_student):
    client.post("/reset-password", data={"email": "student@example.com"})
    with app.app_context():
        token = PasswordResetToken.query.first()
        assert token is not None
        reset_url = f"/reset-password/{token.token}"

    response = client.post(
        reset_url,
        data={"password": "NewPass123!", "confirm_password": "NewPass123!"},
        follow_redirects=True,
    )
    assert b"Password updated successfully" in response.data

    with app.app_context():
        token = PasswordResetToken.query.first()
        assert token.used is True
        assert token.user.verify_password("NewPass123!")


def test_reset_token_expiry(client, app, sample_student):
    with app.app_context():
        expired_token = PasswordResetToken(
            user_id=sample_student.id,
            token="expired",
            created_at=datetime.utcnow() - timedelta(hours=1),
            expires_at=datetime.utcnow() - timedelta(minutes=1),
            used=False,
        )
        db.session.add(expired_token)
        db.session.commit()

    response = client.get("/reset-password/expired", follow_redirects=True)

    assert b"Invalid or expired reset link." in response.data


def test_password_complexity_validation(client, app, sample_student):
    client.post("/reset-password", data={"email": "student@example.com"})
    with app.app_context():
        token = PasswordResetToken.query.first()
        assert token is not None
        reset_url = f"/reset-password/{token.token}"

    response = client.post(
        reset_url,
        data={"password": "short", "confirm_password": "short"},
        follow_redirects=True,
    )

    assert b"Password must be at least 8 characters" in response.data
