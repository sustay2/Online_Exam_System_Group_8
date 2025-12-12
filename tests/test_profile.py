import pytest
from datetime import datetime

from online_exam import db


@pytest.mark.rbac_role("none")
def test_profile_requires_login(client):
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


@pytest.mark.rbac_role("instructor")
def test_profile_shows_user_info(client, sample_instructor):
    response = client.get("/profile")
    assert response.status_code == 200
    assert sample_instructor.email.encode() in response.data
    assert sample_instructor.username.encode() in response.data
    assert sample_instructor.role.encode() in response.data


@pytest.mark.rbac_role("instructor")
def test_enable_two_factor_updates_flag(client, sample_instructor, app):
    response = client.post("/profile/2fa/enable", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = db.session.get(type(sample_instructor), sample_instructor.id)
        assert user.two_factor_enabled is True


@pytest.mark.rbac_role("instructor")
def test_disable_two_factor_clears_fields(client, sample_instructor, app):
    with app.app_context():
        user = db.session.get(type(sample_instructor), sample_instructor.id)
        user.two_factor_enabled = True
        user.otp_code = "dummy"
        user.otp_expires_at = datetime.utcnow()
        db.session.commit()

    response = client.post("/profile/2fa/disable", follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(type(sample_instructor), sample_instructor.id)
        assert user.two_factor_enabled is False
        assert user.otp_code is None
        assert user.otp_expires_at is None
