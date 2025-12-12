import pytest

from online_exam import db
from online_exam.models.login_attempt import LoginAttempt


@pytest.mark.rbac_role("admin")
def test_admin_can_view_login_attempts_page(client, app):
    with app.app_context():
        db.session.add_all(
            [
                LoginAttempt(
                    user_identifier="student@example.com",
                    ip_address="10.0.0.1",
                    success=False,
                ),
                LoginAttempt(
                    user_identifier="instructor@example.com",
                    ip_address="203.0.113.5",
                    success=True,
                ),
            ]
        )
        db.session.commit()

    response = client.get("/analytics/login-attempts")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "student@example.com" in html
    assert "203.0.113.5" in html
    assert "Failed attempts by IP" in html


def test_instructor_cannot_view_login_attempts_page(client):
    response = client.get("/analytics/login-attempts")

    assert response.status_code == 403
