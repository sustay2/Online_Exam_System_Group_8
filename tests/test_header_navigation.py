import pytest


@pytest.mark.rbac_role("instructor")
def test_header_visible_for_authenticated_user(client):
    response = client.get("/exams")
    assert response.status_code == 200
    assert b"Online Exam System" in response.data
    assert b"Profile" in response.data
    assert b"Logout" in response.data


@pytest.mark.rbac_role("none")
def test_header_hidden_on_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Logout" not in response.data
    assert b"Profile" not in response.data


@pytest.mark.rbac_role("none")
def test_header_hidden_on_otp_page(client, sample_instructor):
    sample_instructor.two_factor_enabled = True
    sample_instructor.otp_code = "hashed"
    sample_instructor.otp_expires_at = None
    response = client.get("/auth/verify-otp", follow_redirects=True)
    assert b"Logout" not in response.data


@pytest.mark.rbac_role("admin")
def test_header_shows_username_and_role(client, sample_admin):
    response = client.get("/exams")
    assert sample_admin.name.encode() in response.data
    assert sample_admin.role.encode() in response.data
