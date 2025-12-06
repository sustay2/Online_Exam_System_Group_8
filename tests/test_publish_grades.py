from datetime import datetime

from online_exam import db
from online_exam.models.exam import Exam
from online_exam.models.submission import Submission


def test_publish_grades(client, app):
    # Create exam
    exam = Exam(title="Test Exam", status="draft")
    db.session.add(exam)
    db.session.commit()

    # Create submissions
    sub1 = Submission(
        exam_id=exam.id,
        student_name="Alice",
        status="graded",
        total_score=90,
        max_score=100,
        graded_at=datetime.utcnow(),
    )
    sub2 = Submission(exam_id=exam.id, student_name="Bob", status="pending")
    db.session.add_all([sub1, sub2])
    db.session.commit()

    # Publish grades
    response = client.post(f"/exams/{exam.id}/publish_grades", follow_redirects=True)
    assert b"Grades published successfully" in response.data

    # Refresh from DB
    sub1 = Submission.query.get(sub1.id)
    sub2 = Submission.query.get(sub2.id)

    # Only graded submission is published
    assert sub1.status == "published"
    assert sub2.status == "pending"
