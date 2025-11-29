import pytest

from online_exam.models.question import Question
from online_exam.models.submission import Answer, Submission


def test_submit_exam_page_loads(client, sample_exam):
    """Test that submit exam page loads successfully."""
    response = client.get(f"/exams/{sample_exam.id}/submit")
    assert response.status_code == 200
    assert b"Take Exam" in response.data or sample_exam.title.encode() in response.data


def test_auto_grade_mcq_correct_answer(client, sample_exam, db_session):
    """Test that MCQ is auto-graded correctly when answer is correct."""
    # Create an MCQ question
    question = Question(
        exam_id=sample_exam.id,
        question_text="What is 2 + 2?",
        question_type="mcq",
        points=10,
        option_a="3",
        option_b="4",
        option_c="5",
        option_d="6",
        correct_answer="B",
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit exam with correct answer
    response = client.post(
        f"/exams/{sample_exam.id}/submit",
        data={"student_name": "John Doe", f"question_{question.id}": "B"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Exam submitted successfully!" in response.data

    # Verify submission was created
    submission = Submission.query.filter_by(exam_id=sample_exam.id).first()
    assert submission is not None
    assert submission.student_name == "John Doe"
    assert submission.total_score == 10
    assert submission.max_score == 10
    assert submission.percentage == 100.0
    assert submission.status == "graded"

    # Verify answer was created and graded correctly
    answer = Answer.query.filter_by(submission_id=submission.id, question_id=question.id).first()
    assert answer is not None
    assert answer.selected_option == "B"
    assert answer.is_correct is True
    assert answer.points_earned == 10


def test_auto_grade_mcq_incorrect_answer(client, sample_exam, db_session):
    """Test that MCQ is auto-graded correctly when answer is incorrect."""
    # Create an MCQ question
    question = Question(
        exam_id=sample_exam.id,
        question_text="What is 2 + 2?",
        question_type="mcq",
        points=10,
        option_a="3",
        option_b="4",
        option_c="5",
        option_d="6",
        correct_answer="B",
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit exam with incorrect answer
    response = client.post(
        f"/exams/{sample_exam.id}/submit",
        data={"student_name": "Jane Smith", f"question_{question.id}": "A"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify submission scoring
    submission = Submission.query.filter_by(student_name="Jane Smith").first()
    assert submission.total_score == 0
    assert submission.max_score == 10
    assert submission.percentage == 0.0

    # Verify answer was marked incorrect
    answer = Answer.query.filter_by(submission_id=submission.id).first()
    assert answer.selected_option == "A"
    assert answer.is_correct is False
    assert answer.points_earned == 0


def test_auto_grade_multiple_mcqs(client, sample_exam, db_session):
    """Test auto-grading with multiple MCQ questions."""
    # Create 3 MCQ questions
    q1 = Question(
        exam_id=sample_exam.id,
        question_text="Q1",
        question_type="mcq",
        points=10,
        option_a="A1",
        option_b="B1",
        option_c="C1",
        option_d="D1",
        correct_answer="A",
        order_num=1,
    )
    q2 = Question(
        exam_id=sample_exam.id,
        question_text="Q2",
        question_type="mcq",
        points=15,
        option_a="A2",
        option_b="B2",
        option_c="C2",
        option_d="D2",
        correct_answer="B",
        order_num=2,
    )
    q3 = Question(
        exam_id=sample_exam.id,
        question_text="Q3",
        question_type="mcq",
        points=20,
        option_a="A3",
        option_b="B3",
        option_c="C3",
        option_d="D3",
        correct_answer="C",
        order_num=3,
    )
    db_session.add_all([q1, q2, q3])
    db_session.commit()

    # Submit with 2 correct, 1 incorrect
    response = client.post(
        f"/exams/{sample_exam.id}/submit",
        data={
            "student_name": "Test Student",
            f"question_{q1.id}": "A",  # Correct
            f"question_{q2.id}": "B",  # Correct
            f"question_{q3.id}": "A",  # Incorrect
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify total score: 10 + 15 + 0 = 25/45 = 55.56%
    submission = Submission.query.filter_by(student_name="Test Student").first()
    assert submission.total_score == 25
    assert submission.max_score == 45
    assert submission.percentage == pytest.approx(55.56, rel=0.01)


def test_written_question_not_auto_graded(client, sample_exam, db_session):
    """Test that written questions are not auto-graded."""
    # Create a written question
    question = Question(
        exam_id=sample_exam.id,
        question_text="Explain the water cycle.",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit exam with written answer
    response = client.post(
        f"/exams/{sample_exam.id}/submit",
        data={
            "student_name": "Student A",
            f"question_{question.id}": "The water cycle involves...",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify written answer is saved but not graded
    submission = Submission.query.filter_by(student_name="Student A").first()
    assert submission.total_score == 0  # Not graded yet
    assert submission.max_score == 20

    answer = Answer.query.filter_by(submission_id=submission.id).first()
    assert answer.answer_text == "The water cycle involves..."
    assert answer.is_correct is False
    assert answer.points_earned == 0


def test_view_results_page(client, sample_exam, db_session):
    """Test viewing submission results."""
    # Create submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="View Test",
        total_score=80,
        max_score=100,
        percentage=80.0,
        status="graded",
    )
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/exams/submissions/{submission.id}")
    assert response.status_code == 200
    assert b"Exam Results" in response.data
    assert b"View Test" in response.data
    assert b"80" in response.data


def test_list_submissions_page(client, sample_exam, db_session):
    """Test listing all submissions for an exam."""
    # Create multiple submissions
    s1 = Submission(
        exam_id=sample_exam.id,
        student_name="Student 1",
        total_score=90,
        max_score=100,
        percentage=90.0,
        status="graded",
    )
    s2 = Submission(
        exam_id=sample_exam.id,
        student_name="Student 2",
        total_score=75,
        max_score=100,
        percentage=75.0,
        status="graded",
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/submissions")
    assert response.status_code == 200
    assert b"All Submissions" in response.data or b"Submissions for" in response.data
    assert b"Student 1" in response.data
    assert b"Student 2" in response.data


def test_calculate_percentage(sample_exam, db_session):
    """Test percentage calculation method."""
    submission = Submission(
        exam_id=sample_exam.id, student_name="Test", total_score=75, max_score=100
    )
    db_session.add(submission)
    db_session.commit()

    percentage = submission.calculate_percentage()
    assert percentage == 75.0
    assert submission.percentage == 75.0


def test_percentage_zero_when_max_score_zero(sample_exam, db_session):
    """Test percentage is 0 when max_score is 0."""
    submission = Submission(exam_id=sample_exam.id, student_name="Test", total_score=0, max_score=0)
    db_session.add(submission)
    db_session.commit()

    percentage = submission.calculate_percentage()
    assert percentage == 0.0
