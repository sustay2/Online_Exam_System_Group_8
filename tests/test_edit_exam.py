from datetime import datetime

from online_exam.models.exam import Exam


def create_sample_exam(db):
    exam = Exam(
        title="Original Title",
        description="Original Desc",
        instructions="Original Instructions",
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(exam)
    db.session.commit()
    return exam


# 1. GET edit page loads correctly
def test_edit_exam_form_get(client, app):
    with app.app_context():
        from online_exam import db

        exam = create_sample_exam(db)
        exam_id = exam.id

    response = client.get(f"/exams/{exam_id}/edit")
    assert response.status_code == 200
    assert b"Edit Exam" in response.data


# 2. Valid POST updates the exam
def test_edit_exam_valid_post(client, app):
    with app.app_context():
        from online_exam import db

        exam = create_sample_exam(db)
        exam_id = exam.id

    response = client.post(
        f"/exams/{exam_id}/edit",
        data={
            "title": "Updated Title",
            "description": "Updated Desc",
            "instructions": "Updated Instructions",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Exam updated successfully!" in response.data

    with app.app_context():
        updated = Exam.query.get(exam_id)
        assert updated.title == "Updated Title"
        assert updated.description == "Updated Desc"
        assert updated.instructions == "Updated Instructions"


# 3. Missing title returns validation error
def test_edit_exam_missing_title(client, app):
    with app.app_context():
        from online_exam import db

        exam = create_sample_exam(db)
        exam_id = exam.id

        exam = create_sample_exam(db)

    response = client.post(
        f"/exams/{exam_id}/edit",
        data={
            "title": "",
            "description": "Something",
            "instructions": "Something",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Title is required." in response.data


# 4. Editing non-existing exam returns 404
def test_edit_exam_not_found(client):
    response = client.get("/exams/999/edit")
    assert response.status_code == 404
