import pytest

from online_exam.models.exam import Exam
from online_exam.models.question import Question



def test_edit_question_page_loads(client, sample_question):
    """Test that edit question page loads successfully."""
    response = client.get(f"/exams/{sample_question.exam_id}/questions/{sample_question.id}/edit")
    assert response.status_code == 200
    assert b"Edit Question" in response.data
    assert sample_question.question_text.encode() in response.data


def test_edit_written_question_success(client, sample_question, db_session):
    """Test successfully editing a written question."""
    response = client.post(
        f"/exams/{sample_question.exam_id}/questions/{sample_question.id}/edit",
        data={"question_text": "Updated question text", "points": 15},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Question updated successfully!" in response.data

    # Verify question was updated
    updated_question = Question.query.get(sample_question.id)  # ← THIS LINE INSIDE FUNCTION
    assert updated_question.question_text == "Updated question text"
    assert updated_question.points == 15


def test_edit_mcq_question_success(client, sample_exam, db_session):
    """Test successfully editing an MCQ question."""
    # Create an MCQ question
    question = Question(
        exam_id=sample_exam.id,
        question_text="What is 2 + 2?",
        question_type="mcq",
        points=5,
        option_a="3",
        option_b="4",
        option_c="5",
        option_d="6",
        correct_answer="B",
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Edit the question
    response = client.post(
        f"/exams/{sample_exam.id}/questions/{question.id}/edit",
        data={
            "question_text": "What is 3 + 3?",
            "points": 10,
            "option_a": "5",
            "option_b": "6",
            "option_c": "7",
            "option_d": "8",
            "correct_answer": "B",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Question updated successfully!" in response.data

    # Verify question was updated
    db_session.refresh(question)
    assert question.question_text == "What is 3 + 3?"
    assert question.points == 10
    assert question.option_a == "5"
    assert question.option_b == "6"


def test_edit_question_missing_text(client, sample_question, db_session):
    """Test editing question with missing text shows error."""
    original_text = sample_question.question_text

    response = client.post(
        f"/exams/{sample_question.exam_id}/questions/{sample_question.id}/edit",
        data={"question_text": "", "points": 10},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Question text is required" in response.data

    # Verify question was not updated
    unchanged_question = Question.query.get(sample_question.id)
    assert unchanged_question.question_text == original_text


def test_edit_mcq_missing_option(client, sample_exam, db_session):
    """Test editing MCQ without all options shows error."""
    # Create an MCQ question
    question = Question(
        exam_id=sample_exam.id,
        question_text="What is 2 + 2?",
        question_type="mcq",
        points=5,
        option_a="3",
        option_b="4",
        option_c="5",
        option_d="6",
        correct_answer="B",
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Try to edit with missing option
    response = client.post(
        f"/exams/{sample_exam.id}/questions/{question.id}/edit",
        data={
            "question_text": "What is 2 + 2?",
            "points": 5,
            "option_a": "3",
            "option_b": "4",
            "option_c": "",  # Missing
            "option_d": "6",
            "correct_answer": "B",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"All four options are required" in response.data


def test_cannot_edit_published_exam_question(client, db_session, sample_instructor):
    """Test that questions in published exams cannot be edited."""
    # Create a published exam
    exam = Exam(
    title="Published Exam",
    description="Test Description",
    instructions="Test instructions",
    status="published",
    )    
    db_session.add(exam)
    db_session.commit()

    # Create a question
    question = Question(
        exam_id=exam.id, question_text="Test question", question_type="written", points=10, order_num=1
    )
    db_session.add(question)
    db_session.commit()

    # Try to edit
    response = client.post(
        f"/exams/{exam.id}/questions/{question.id}/edit",
        data={"question_text": "Updated text", "points": 15},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Cannot edit questions in a published exam" in response.data

    # Verify question was not updated
    db_session.refresh(question)
    assert question.question_text == "Test question"


def test_delete_question_success(client, sample_question, db_session):
    """Test successfully deleting a question."""
    question_id = sample_question.id
    exam_id = sample_question.exam_id

    response = client.post(f"/exams/{exam_id}/questions/{question_id}/delete", follow_redirects=True)

    assert response.status_code == 200
    assert b"Question deleted successfully!" in response.data

    # Verify question was deleted
    question = Question.query.get(question_id)
    assert question is None


def test_cannot_delete_published_exam_question(client, db_session, sample_instructor):
    """Test that questions in published exams cannot be deleted."""
    # Create a published exam
    exam = Exam(
    title="Published Exam",
    description="Test Description",
    instructions="Test instructions",
    status="published",
)
    db_session.add(exam)
    db_session.commit()

    # Create a question
    question = Question(
        exam_id=exam.id, question_text="Test question", question_type="written", points=10, order_num=1
    )
    db_session.add(question)
    db_session.commit()

    # Try to delete
    response = client.post(f"/exams/{exam.id}/questions/{question.id}/delete", follow_redirects=True)

    assert response.status_code == 200
    assert b"Cannot delete questions from a published exam" in response.data

    # Verify question still exists
    db_session.refresh(question)
    assert question is not None


def test_delete_nonexistent_question_404(client, sample_exam):
    """Test deleting a non-existent question returns 404."""
    response = client.post(f"/exams/{sample_exam.id}/questions/99999/delete")
    assert response.status_code == 404