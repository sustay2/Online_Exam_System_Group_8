from models.exam import Exam
from app import db

# ---------- 1. GET /exams/create shows the form ----------

def test_create_exam_form_get(client):
    response = client.get("/exams/create")
    assert response.status_code == 200
    assert b"Create Exam" in response.data


# ---------- 2. POST /exams/create with valid data saves a draft ----------

def test_create_exam_valid_post_creates_draft(client):
    response = client.post(
        "/exams/create",
        data={
            "title": "Midterm Test",
            "description": "Covers chapters 1\u20113",
            "instructions": "Answer all questions."
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Draft exam created successfully!" in response.data

    exam = Exam.query.filter_by(title="Midterm Test").first()
    assert exam is not None
    assert exam.status == "draft"
    assert exam.description == "Covers chapters 1\u20113"
    assert exam.instructions == "Answer all questions."


# ---------- 3. POST /exams/create without title -> validation error ----------

def test_create_exam_missing_title_shows_error(client):
    response = client.post(
        "/exams/create",
        data={
            "title": "",
            "description": "Desc",
            "instructions": "Instr"
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    assert b"Title is required." in response.data

    assert Exam.query.count() == 0