import pytest

from online_exam.models.question import Question
from online_exam.models.submission import Answer, Submission


def test_manual_grade_page_loads(client, sample_exam, db_session):
    """Test that manual grading page loads successfully."""
    # Create submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Test Student",
        total_score=0,
        max_score=20,
        status="pending",
    )
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/exams/submissions/{submission.id}/grade")
    assert response.status_code == 200
    assert b"Manual Grading" in response.data
    assert b"Test Student" in response.data


def test_manual_grade_written_question(client, sample_exam, db_session):
    """Test manually grading a written question."""
    # Create written question
    question = Question(
        exam_id=sample_exam.id,
        question_text="Explain the water cycle.",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Create submission with answer
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Student A",
        total_score=0,
        max_score=20,
        status="pending",
    )
    db_session.add(submission)
    db_session.flush()

    answer = Answer(
        submission_id=submission.id,
        question_id=question.id,
        answer_text="The water cycle involves evaporation, condensation, and precipitation.",
        points_earned=0,
    )
    db_session.add(answer)
    db_session.commit()

    # Grade the answer
    response = client.post(
        f"/exams/submissions/{submission.id}/grade",
        data={
            f"points_{answer.id}": "18",
            f"comment_{answer.id}": "Good explanation, but missing some details.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Grading saved successfully!" in response.data

    # Verify grading was saved
    db_session.refresh(answer)
    assert answer.points_earned == 18
    assert answer.instructor_comment == "Good explanation, but missing some details."

    db_session.refresh(submission)
    assert submission.total_score == 18
    assert submission.max_score == 20
    assert submission.percentage == 90.0
    assert submission.status == "graded"


def test_manual_grade_multiple_written_questions(client, sample_exam, db_session):
    """Test grading multiple written questions."""
    # Create 2 written questions
    q1 = Question(
        exam_id=sample_exam.id,
        question_text="Question 1",
        question_type="written",
        points=15,
        order_num=1,
    )
    q2 = Question(
        exam_id=sample_exam.id,
        question_text="Question 2",
        question_type="written",
        points=25,
        order_num=2,
    )
    db_session.add_all([q1, q2])
    db_session.commit()

    # Create submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Student B",
        total_score=0,
        max_score=40,
        status="pending",
    )
    db_session.add(submission)
    db_session.flush()

    # Create answers
    a1 = Answer(
        submission_id=submission.id, question_id=q1.id, answer_text="Answer 1", points_earned=0
    )
    a2 = Answer(
        submission_id=submission.id, question_id=q2.id, answer_text="Answer 2", points_earned=0
    )
    db_session.add_all([a1, a2])
    db_session.commit()

    # Grade both answers
    response = client.post(
        f"/exams/submissions/{submission.id}/grade",
        data={
            f"points_{a1.id}": "12",
            f"comment_{a1.id}": "Good work",
            f"points_{a2.id}": "20",
            f"comment_{a2.id}": "Needs improvement",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify total score: 12 + 20 = 32/40 = 80%
    db_session.refresh(submission)
    assert submission.total_score == 32
    assert submission.max_score == 40
    assert submission.percentage == 80.0


def test_manual_grade_mixed_mcq_and_written(client, sample_exam, db_session):
    """Test grading submission with both MCQ (auto-graded) and written questions."""
    # Create MCQ question
    mcq = Question(
        exam_id=sample_exam.id,
        question_text="MCQ Question",
        question_type="mcq",
        points=10,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="B",
        order_num=1,
    )
    # Create written question
    written = Question(
        exam_id=sample_exam.id,
        question_text="Written Question",
        question_type="written",
        points=20,
        order_num=2,
    )
    db_session.add_all([mcq, written])
    db_session.commit()

    # Create submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Student C",
        total_score=10,  # MCQ already graded
        max_score=30,
        status="pending",
    )
    db_session.add(submission)
    db_session.flush()

    # MCQ answer (already graded)
    mcq_answer = Answer(
        submission_id=submission.id,
        question_id=mcq.id,
        selected_option="B",
        is_correct=True,
        points_earned=10,
    )
    # Written answer (needs grading)
    written_answer = Answer(
        submission_id=submission.id,
        question_id=written.id,
        answer_text="My written answer",
        points_earned=0,
    )
    db_session.add_all([mcq_answer, written_answer])
    db_session.commit()

    # Grade the written answer
    response = client.post(
        f"/exams/submissions/{submission.id}/grade",
        data={f"points_{written_answer.id}": "15", f"comment_{written_answer.id}": "Good answer"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify total score: 10 (MCQ) + 15 (written) = 25/30 = 83.33%
    db_session.refresh(submission)
    assert submission.total_score == 25
    assert submission.max_score == 30
    assert submission.percentage == pytest.approx(83.33, rel=0.01)


def test_manual_grade_points_validation(client, sample_exam, db_session):
    """Test that points awarded cannot exceed maximum points."""
    # Create written question worth 10 points
    question = Question(
        exam_id=sample_exam.id,
        question_text="Question",
        question_type="written",
        points=10,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Student D",
        total_score=0,
        max_score=10,
        status="pending",
    )
    db_session.add(submission)
    db_session.flush()

    answer = Answer(
        submission_id=submission.id, question_id=question.id, answer_text="Answer", points_earned=0
    )
    db_session.add(answer)
    db_session.commit()

    # Try to award 15 points (more than max of 10)
    response = client.post(
        f"/exams/submissions/{submission.id}/grade",
        data={f"points_{answer.id}": "15", f"comment_{answer.id}": "Excellent"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify points were capped at maximum
    db_session.refresh(answer)
    assert answer.points_earned == 10  # Should be capped at max points


def test_view_results_shows_instructor_comments(client, sample_exam, db_session):
    """Test that view results page shows instructor comments."""
    # Create written question
    question = Question(
        exam_id=sample_exam.id,
        question_text="Question",
        question_type="written",
        points=10,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Student E",
        total_score=8,
        max_score=10,
        percentage=80.0,
        status="graded",
    )
    db_session.add(submission)
    db_session.flush()

    answer = Answer(
        submission_id=submission.id,
        question_id=question.id,
        answer_text="My answer",
        points_earned=8,
        instructor_comment="Great work! Just missing one detail.",
    )
    db_session.add(answer)
    db_session.commit()

    response = client.get(f"/exams/submissions/{submission.id}")
    assert response.status_code == 200
    assert b"Great work! Just missing one detail." in response.data
    assert b"Instructor Feedback" in response.data


def test_manual_grade_updates_existing_grade(client, sample_exam, db_session):
    """Test that manual grading can update previously graded answers."""
    question = Question(
        exam_id=sample_exam.id,
        question_text="Question",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Student F",
        total_score=15,
        max_score=20,
        status="graded",
    )
    db_session.add(submission)
    db_session.flush()

    answer = Answer(
        submission_id=submission.id,
        question_id=question.id,
        answer_text="Answer",
        points_earned=15,
        instructor_comment="Good",
    )
    db_session.add(answer)
    db_session.commit()

    # Re-grade with different score
    response = client.post(
        f"/exams/submissions/{submission.id}/grade",
        data={
            f"points_{answer.id}": "18",
            f"comment_{answer.id}": "Actually, this is better than I thought",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify grade was updated
    db_session.refresh(answer)
    assert answer.points_earned == 18
    assert answer.instructor_comment == "Actually, this is better than I thought"

    db_session.refresh(submission)
    assert submission.total_score == 18
