from datetime import datetime

from online_exam import db
from online_exam.models.exam import Exam


def test_schedule_exam_get_form(client, app):
    # Create a draft exam
    with app.app_context():
        exam = Exam(title="Math Test", description="Chap 1-5", instructions="Do all")
        db.session.add(exam)
        db.session.commit()
        exam_id = exam.id

    # Test GET request
    response = client.get(f"/exams/schedule/{exam_id}")
    assert response.status_code == 200
    assert b"Schedule Exam" in response.data


def test_schedule_exam_post_success(client, app):
    with app.app_context():
        exam = Exam(title="Physics", description="Chapters", instructions="Do all")
        db.session.add(exam)
        db.session.commit()
        exam_id = exam.id

    data = {
        "start_time": "2025-12-01T09:00",
        "end_time": "2025-12-01T11:00",
    }

    response = client.post(
        f"/exams/schedule/{exam_id}",
        data=data,
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Exam scheduled successfully!" in response.data

    # Verify DB update
    with app.app_context():
        exam = db.session.get(Exam, exam_id)
        assert exam.start_time == datetime(2025, 12, 1, 9, 0)
        assert exam.end_time == datetime(2025, 12, 1, 11, 0)


def test_schedule_exam_missing_fields(client, app):
    with app.app_context():
        exam = Exam(title="English", description="", instructions="")
        db.session.add(exam)
        db.session.commit()
        exam_id = exam.id

    data = {
        "start_time": "",
        "end_time": "",
    }

    response = client.post(
        f"/exams/schedule/{exam_id}",
        data=data,
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Start and end time are required." in response.data
