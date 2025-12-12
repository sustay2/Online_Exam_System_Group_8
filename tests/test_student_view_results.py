import pytest

from online_exam.models.exam import Exam
from online_exam.models.question import Question
from online_exam.models.submission import Answer, Submission


pytestmark = pytest.mark.rbac_role("student")


def test_view_results_page(client, db_session):
    """Test that student can view results page after submission."""
    # Create exam
    exam = Exam(title="Sample Exam", status="published")
    db_session.add(exam)
    db_session.flush()

    # Create questions
    mcq = Question(
        exam_id=exam.id,
        question_text="MCQ Q1",
        question_type="mcq",
        points=5,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="A",
        order_num=1,
    )
    written = Question(
        exam_id=exam.id,
        question_text="Written Q1",
        question_type="written",  # Added to fix NOT NULL constraint
        points=10,
        order_num=2,
    )
    db_session.add_all([mcq, written])
    db_session.flush()

    # Create submission
    submission = Submission(
        exam_id=exam.id, student_name="Test Student", status="graded", total_score=13, max_score=15
    )
    db_session.add(submission)
    db_session.flush()

    # Add answers
    mcq_answer = Answer(
        submission_id=submission.id,
        question_id=mcq.id,
        selected_option="A",
        is_correct=True,
        points_earned=5,
    )
    written_answer = Answer(
        submission_id=submission.id,
        question_id=written.id,
        answer_text="My answer",
        points_earned=8,
        instructor_comment="Well done",
    )
    db_session.add_all([mcq_answer, written_answer])
    db_session.commit()

    response = client.get(f"/student/submissions/{submission.id}/results")
    assert response.status_code == 200
    assert b"Sample Exam" in response.data
    assert b"Test Student" in response.data
    assert b"MCQ Q1" in response.data
    assert b"Written Q1" in response.data
    assert b"Well done" in response.data


def test_view_results_not_published(client, db_session):
    """Test viewing results when grades are not yet available."""
    exam = Exam(title="Pending Exam", status="published")
    db_session.add(exam)
    db_session.flush()

    submission = Submission(exam_id=exam.id, student_name="Student 1", status="pending")
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/student/submissions/{submission.id}/results", follow_redirects=True)
    assert response.status_code == 200
    assert b"Grading In Progress" in response.data or b"pending" in response.data.lower()
