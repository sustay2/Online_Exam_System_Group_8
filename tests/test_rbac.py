import pytest


pytestmark = pytest.mark.rbac_role("none")


def test_anonymous_redirected_from_protected_routes(client):
    exams_response = client.get("/exams")
    student_response = client.get("/student/dashboard")

    assert exams_response.status_code == 302
    assert "/login" in exams_response.headers["Location"]
    assert student_response.status_code == 302
    assert "/login" in student_response.headers["Location"]


def test_student_only_has_access_to_student_routes(client, sample_student, sample_exam, login_user):
    login_user(sample_student)

    student_dashboard = client.get("/student/dashboard")
    exams_response = client.get("/exams")
    analytics_response = client.get(f"/analytics/exams/{sample_exam.id}/report")

    assert student_dashboard.status_code == 200
    assert exams_response.status_code == 403
    assert analytics_response.status_code == 403


def test_instructor_blocked_from_student_routes(client, sample_instructor, sample_exam, login_user):
    login_user(sample_instructor)

    exams_response = client.get("/exams")
    analytics_response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    student_dashboard = client.get("/student/dashboard")

    assert exams_response.status_code == 200
    assert analytics_response.status_code == 200
    assert student_dashboard.status_code == 403


def test_admin_blocked_from_student_routes(client, sample_admin, sample_exam, login_user):
    login_user(sample_admin)

    exams_response = client.get("/exams")
    analytics_response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    student_dashboard = client.get("/student/dashboard")

    assert exams_response.status_code == 200
    assert analytics_response.status_code == 200
    assert student_dashboard.status_code == 403
