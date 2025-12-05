"""
Tests for Story 3: Student Take Exam

User Story:
As a student, I want to take the exam online so that I can complete and submit my answers digitally.

Acceptance Criteria:
1. Student can view exam in full-view mode
2. Leave page warning shown before navigating away
3. All responses saved on submission
4. Confirmation message after submission
"""

from online_exam.models.question import Question
from online_exam.models.submission import Answer, Submission


# ============================================================================
# STORY 3 - TEST 1: Display Take Exam Page
# ============================================================================


def test_take_exam_page_loads_for_published_exam(client, sample_exam, db_session):
    """Test that take exam page loads successfully for published exams."""
    # Publish the exam
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200
    assert b"Take Exam" in response.data or sample_exam.title.encode() in response.data
    assert b"Student Information" in response.data


def test_take_exam_redirects_for_draft_exam(client, sample_exam, db_session):
    """Test that draft exams cannot be taken by students."""
    # Ensure exam is draft
    sample_exam.status = "draft"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take", follow_redirects=True)
    assert response.status_code == 200
    assert b"not available yet" in response.data


def test_take_exam_displays_all_questions(client, sample_exam, db_session):
    """Test that all questions are displayed on the take exam page."""
    # Publish exam
    sample_exam.status = "published"

    # Create MCQ question
    mcq = Question(
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

    # Create written question
    written = Question(
        exam_id=sample_exam.id,
        question_text="Explain the water cycle.",
        question_type="written",
        points=20,
        order_num=2,
    )

    db_session.add_all([mcq, written])
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200
    assert b"What is 2 + 2?" in response.data
    assert b"Explain the water cycle." in response.data
    assert b"30" in response.data  # Total points


def test_take_exam_shows_exam_info(client, sample_exam, db_session):
    """Test that exam info (title, description, instructions) is displayed."""
    sample_exam.status = "published"
    sample_exam.description = "Test Description"
    sample_exam.instructions = "Test Instructions"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200
    assert b"Test Description" in response.data
    assert b"Test Instructions" in response.data


# ============================================================================
# STORY 3 - TEST 2: Submit Exam with Answers
# ============================================================================


def test_submit_exam_with_student_name_required(client, sample_exam, db_session):
    """Test that student name is required for submission."""
    sample_exam.status = "published"
    db_session.commit()

    # Try to submit without student name
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": ""},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Student name is required" in response.data

    # Verify no submission was created
    assert Submission.query.count() == 0


def test_submit_exam_creates_submission_record(client, sample_exam, db_session):
    """Test that submitting exam creates a submission record."""
    sample_exam.status = "published"

    # Create a question
    question = Question(
        exam_id=sample_exam.id,
        question_text="Test Question",
        question_type="written",
        points=10,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit exam
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "John Doe", f"question_{question.id}": "My answer"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Exam submitted successfully!" in response.data

    # Verify submission was created
    submission = Submission.query.filter_by(student_name="John Doe").first()
    assert submission is not None
    assert submission.exam_id == sample_exam.id
    assert submission.status == "graded"


def test_submit_exam_auto_grades_mcq(client, sample_exam, db_session):
    """Test that MCQ questions are auto-graded on submission."""
    sample_exam.status = "published"

    # Create MCQ question
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

    # Submit with correct answer
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "Jane Doe", f"question_{question.id}": "B"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify auto-grading
    submission = Submission.query.filter_by(student_name="Jane Doe").first()
    assert submission.total_score == 10
    assert submission.max_score == 10
    assert submission.percentage == 100.0

    # Verify answer was marked correct
    answer = Answer.query.filter_by(submission_id=submission.id).first()
    assert answer.selected_option == "B"
    assert answer.is_correct is True
    assert answer.points_earned == 10


def test_submit_exam_saves_written_answers(client, sample_exam, db_session):
    """Test that written answers are saved without auto-grading."""
    sample_exam.status = "published"

    # Create written question
    question = Question(
        exam_id=sample_exam.id,
        question_text="Explain photosynthesis.",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit with written answer
    answer_text = "Photosynthesis is the process by which plants convert light into energy."
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "Alice Smith", f"question_{question.id}": answer_text},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify written answer was saved
    submission = Submission.query.filter_by(student_name="Alice Smith").first()
    answer = Answer.query.filter_by(submission_id=submission.id).first()
    assert answer.answer_text == answer_text
    assert answer.points_earned == 0  # Not graded yet
    assert answer.is_correct is False


def test_submit_exam_with_mixed_questions(client, sample_exam, db_session):
    """Test submitting exam with both MCQ and written questions."""
    sample_exam.status = "published"

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
        correct_answer="A",
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

    # Submit with both answers
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={
            "student_name": "Bob Johnson",
            f"question_{mcq.id}": "A",  # Correct
            f"question_{written.id}": "My written answer",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify grading
    submission = Submission.query.filter_by(student_name="Bob Johnson").first()
    assert submission.total_score == 10  # Only MCQ graded
    assert submission.max_score == 30  # MCQ + Written
    # Use abs() instead of pytest.approx for pytest-rich compatibility
    assert abs(submission.percentage - 33.33) < 0.01


# ============================================================================
# STORY 3 - TEST 3: View Results Page
# ============================================================================


def test_view_results_page_loads(client, sample_exam, db_session):
    """Test that results page loads successfully."""
    # Create submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Test Student",
        total_score=80,
        max_score=100,
        percentage=80.0,
        status="graded",
    )
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/student/submissions/{submission.id}/results")
    assert response.status_code == 200
    assert b"Exam Results" in response.data
    assert b"Test Student" in response.data
    assert b"80" in response.data  # Score percentage


def test_view_results_shows_mcq_answers(client, sample_exam, db_session):
    """Test that results page shows MCQ answers and correct answers."""
    # Create MCQ question
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
    db_session.flush()

    # Create submission with incorrect answer
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Test Student",
        total_score=0,
        max_score=10,
        percentage=0.0,
        status="graded",
    )
    db_session.add(submission)
    db_session.flush()

    # Create answer
    answer = Answer(
        submission_id=submission.id,
        question_id=question.id,
        selected_option="A",
        is_correct=False,
        points_earned=0,
    )
    db_session.add(answer)
    db_session.commit()

    response = client.get(f"/student/submissions/{submission.id}/results")
    assert response.status_code == 200
    assert b"Your Answer" in response.data
    assert b"Correct Answer" in response.data
    assert b"A" in response.data  # Student's answer
    assert b"B" in response.data  # Correct answer


def test_view_results_shows_written_answers(client, sample_exam, db_session):
    """Test that results page shows written answers."""
    # Create written question
    question = Question(
        exam_id=sample_exam.id,
        question_text="Explain the water cycle.",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.flush()

    # Create submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Test Student",
        total_score=0,
        max_score=20,
        percentage=0.0,
        status="graded",
    )
    db_session.add(submission)
    db_session.flush()

    # Create answer
    answer = Answer(
        submission_id=submission.id,
        question_id=question.id,
        answer_text="The water cycle involves evaporation and condensation.",
        points_earned=0,
    )
    db_session.add(answer)
    db_session.commit()

    response = client.get(f"/student/submissions/{submission.id}/results")
    assert response.status_code == 200
    assert b"The water cycle involves evaporation and condensation." in response.data
    assert b"Awaiting Manual Grading" in response.data or b"pending" in response.data.lower()


def test_view_results_shows_performance_badge(client, sample_exam, db_session):
    """Test that results page shows appropriate performance badge."""
    # Create submission with high score
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Excellent Student",
        total_score=85,
        max_score=100,
        percentage=85.0,
        status="graded",
    )
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/student/submissions/{submission.id}/results")
    assert response.status_code == 200
    assert b"Excellent" in response.data  # Should show "Excellent" badge


def test_view_results_shows_instructor_feedback(client, sample_exam, db_session):
    """Test that results page shows instructor feedback for written questions."""
    # Create written question
    question = Question(
        exam_id=sample_exam.id,
        question_text="Written Question",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.flush()

    # Create submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Test Student",
        total_score=18,
        max_score=20,
        percentage=90.0,
        status="graded",
    )
    db_session.add(submission)
    db_session.flush()

    # Create answer with instructor comment
    answer = Answer(
        submission_id=submission.id,
        question_id=question.id,
        answer_text="My answer",
        points_earned=18,
        instructor_comment="Great work! Just missing one detail.",
    )
    db_session.add(answer)
    db_session.commit()

    response = client.get(f"/student/submissions/{submission.id}/results")
    assert response.status_code == 200
    assert b"Great work! Just missing one detail." in response.data
    assert b"Instructor Feedback" in response.data


# ============================================================================
# STORY 3 - TEST 4: Submission Flow Integration
# ============================================================================


def test_full_exam_submission_flow(client, sample_exam, db_session):
    """Test complete flow: take exam -> submit -> view results."""
    # Setup: Publish exam with questions
    sample_exam.status = "published"

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

    written = Question(
        exam_id=sample_exam.id,
        question_text="Written Question",
        question_type="written",
        points=20,
        order_num=2,
    )

    db_session.add_all([mcq, written])
    db_session.commit()

    # Step 1: Load take exam page
    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Step 2: Submit exam
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={
            "student_name": "Integration Test",
            f"question_{mcq.id}": "B",  # Correct
            f"question_{written.id}": "My written answer",
        },
        follow_redirects=False,
    )

    # Should redirect to results
    assert response.status_code == 302
    assert "/student/submissions/" in response.location

    # Step 3: Follow redirect to results
    response = client.get(response.location)
    assert response.status_code == 200
    assert b"Exam Results" in response.data
    assert b"Integration Test" in response.data


def test_submission_calculates_percentage_correctly(client, sample_exam, db_session):
    """Test that submission calculates percentage correctly."""
    sample_exam.status = "published"

    # Create questions totaling 50 points
    q1 = Question(
        exam_id=sample_exam.id,
        question_text="Q1",
        question_type="mcq",
        points=20,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="A",
        order_num=1,
    )
    q2 = Question(
        exam_id=sample_exam.id,
        question_text="Q2",
        question_type="mcq",
        points=30,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="B",
        order_num=2,
    )
    db_session.add_all([q1, q2])
    db_session.commit()

    # Submit with 1 correct, 1 incorrect
    client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={
            "student_name": "Percent Test",
            f"question_{q1.id}": "A",  # Correct (20 points)
            f"question_{q2.id}": "A",  # Incorrect (0 points)
        },
        follow_redirects=True,
    )

    submission = Submission.query.filter_by(student_name="Percent Test").first()
    assert submission.total_score == 20
    assert submission.max_score == 50
    assert submission.percentage == 40.0


# ============================================================================
# STORY 3 - TEST 5: Edge Cases
# ============================================================================


def test_submit_exam_with_empty_written_answer(client, sample_exam, db_session):
    """Test submitting with empty written answer."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="Written Question",
        question_type="written",
        points=10,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit with empty answer
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "Empty Answer", f"question_{question.id}": ""},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify answer was saved as empty
    submission = Submission.query.filter_by(student_name="Empty Answer").first()
    answer = Answer.query.filter_by(submission_id=submission.id).first()
    assert answer.answer_text == ""


def test_submit_exam_without_selecting_mcq(client, sample_exam, db_session):
    """Test submitting without selecting MCQ answer (HTML5 validation should prevent this)."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="MCQ Question",
        question_type="mcq",
        points=10,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="A",
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit without MCQ answer (form data missing)
    client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "No MCQ Answer"},
        follow_redirects=True,
    )

    # Should still create submission (backend doesn't strictly require MCQ answer)
    submission = Submission.query.filter_by(student_name="No MCQ Answer").first()
    assert submission is not None
    assert submission.total_score == 0


def test_view_results_for_nonexistent_submission(client):
    """Test viewing results for non-existent submission returns 404."""
    response = client.get("/student/submissions/99999/results")
    assert response.status_code == 404
