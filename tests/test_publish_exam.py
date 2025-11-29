# tests/test_publish_exam.py
from online_exam.models.exam import Exam


def test_publish_exam(client, app):
    # 1. Create a draft exam directly in the database
    with app.app_context():
        exam = Exam(title="Physics Final", description="Test", status="draft")
        from online_exam import db

        db.session.add(exam)
        db.session.commit()
        exam_id = exam.id

    # 2. Log in as instructor (adjust credentials to match your real login)
    client.post(
        "/login",
        data={
            "username": "instructor",
            "password": "password",
        },  # change if your test user is different
        follow_redirects=True,
    )

    # 3. Publish the exam
    response = client.post(f"/exams/{exam_id}/publish", follow_redirects=True)
    assert response.status_code == 200
    assert b"published successfully" in response.data

    # 4. Verify status changed in DB
    with app.app_context():
        exam = Exam.query.get(exam_id)
        assert exam.status == "published"

    # 5. Try to edit → must be blocked
    response = client.get(f"/exams/{exam_id}/edit")
    assert response.status_code == 302  # redirect
    follow = client.get(response.location, follow_redirects=True)
    assert b"Cannot edit a published exam" in follow.data
