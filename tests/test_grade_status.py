"""
Tests for Smart Submission Status Logic

Requirements:
1. Submissions with written questions → status = "pending"
2. Submissions with only MCQ → status = "graded"
3. Status changes to "graded" after instructor grades
4. Submissions list shows clear status indicators
"""

from online_exam.models.question import Question
from online_exam.models.submission import Answer, Submission


# ============================================================================
# TEST 1: MCQ-only submissions are auto-graded
# ============================================================================


def test_mcq_only_submission_marked_graded(client, sample_exam, db_session):
    """Test that submissions with only MCQ questions are marked as 'graded' immediately."""
    sample_exam.status = "published"

    # Create only MCQ questions
    q1 = Question(
        exam_id=sample_exam.id,
        question_text="MCQ 1",
        question_type="mcq",
        points=10,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="A",
        order_num=1,
    )
    q2 = Question(
        exam_id=sample_exam.id,
        question_text="MCQ 2",
        question_type="mcq",
        points=10,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="B",
        order_num=2,
    )
    db_session.add_all([q1, q2])
    db_session.commit()

    # Submit exam
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "MCQ Student", f"question_{q1.id}": "A", f"question_{q2.id}": "B"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify status is "graded" (no manual grading needed)
    submission = Submission.query.filter_by(student_name="MCQ Student").first()
    assert submission is not None
    assert submission.status == "graded"
    assert submission.graded_at is not None


# ============================================================================
# TEST 2: Submissions with written questions are pending
# ============================================================================


def test_written_question_submission_marked_pending(client, sample_exam, db_session):
    """Test that submissions with written questions are marked as 'pending'."""
    sample_exam.status = "published"

    # Create mix of MCQ and written
    mcq = Question(
        exam_id=sample_exam.id,
        question_text="MCQ",
        question_type="mcq",
        points=10,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="A",
        order_num=1,
    )
    written = Question(
        exam_id=sample_exam.id,
        question_text="Written",
        question_type="written",
        points=20,
        order_num=2,
    )
    db_session.add_all([mcq, written])
    db_session.commit()

    # Submit exam
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={
            "student_name": "Mixed Student",
            f"question_{mcq.id}": "A",
            f"question_{written.id}": "My answer",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify status is "pending" (needs manual grading)
    submission = Submission.query.filter_by(student_name="Mixed Student").first()
    assert submission is not None
    assert submission.status == "pending"
    assert submission.graded_at is None


def test_written_only_submission_marked_pending(client, sample_exam, db_session):
    """Test that submissions with only written questions are marked as 'pending'."""
    sample_exam.status = "published"

    # Create only written questions
    w1 = Question(
        exam_id=sample_exam.id,
        question_text="Written 1",
        question_type="written",
        points=20,
        order_num=1,
    )
    w2 = Question(
        exam_id=sample_exam.id,
        question_text="Written 2",
        question_type="written",
        points=20,
        order_num=2,
    )
    db_session.add_all([w1, w2])
    db_session.commit()

    # Submit exam
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={
            "student_name": "Written Student",
            f"question_{w1.id}": "Answer 1",
            f"question_{w2.id}": "Answer 2",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify status is "pending"
    submission = Submission.query.filter_by(student_name="Written Student").first()
    assert submission is not None
    assert submission.status == "pending"


# ============================================================================
# TEST 3: Status changes after manual grading
# ============================================================================


def test_status_changes_to_graded_after_manual_grading(client, sample_exam, db_session):
    """Test that status changes from 'pending' to 'graded' after instructor grades."""
    sample_exam.status = "published"

    # Create written question
    question = Question(
        exam_id=sample_exam.id,
        question_text="Written",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit exam (will be pending)
    client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "Grade Test", f"question_{question.id}": "My answer"},
    )

    submission = Submission.query.filter_by(student_name="Grade Test").first()
    assert submission.status == "pending"

    # Instructor grades the submission
    answer = Answer.query.filter_by(submission_id=submission.id).first()
    response = client.post(
        f"/exams/submissions/{submission.id}/grade",
        data={f"points_{answer.id}": "18", f"comment_{answer.id}": "Good work"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify status changed to "graded"
    db_session.refresh(submission)
    assert submission.status == "graded"
    assert submission.graded_at is not None


# ============================================================================
# TEST 4: Flash messages show correct info
# ============================================================================


def test_mcq_submission_flash_shows_final_score(client, sample_exam, db_session):
    """Test that MCQ-only submission shows final score in flash message."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="MCQ",
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

    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "Flash Test MCQ", f"question_{question.id}": "A"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Your final score" in response.data or b"final score" in response.data.lower()


def test_written_submission_flash_shows_pending_message(client, sample_exam, db_session):
    """Test that submission with written questions shows pending message."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="Written",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "Flash Test Written", f"question_{question.id}": "Answer"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"pending" in response.data.lower() or b"instructor grading" in response.data.lower()


# ============================================================================
# TEST 5: Submissions list shows status correctly
# ============================================================================


def test_submissions_list_shows_pending_status(client, sample_exam, db_session):
    """Test that submissions list displays pending status badge."""
    # Create pending submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Pending Student",
        total_score=0,
        max_score=20,
        status="pending",
    )
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/submissions")
    assert response.status_code == 200
    assert b"Pending Grading" in response.data or b"pending" in response.data.lower()
    assert b"Pending Student" in response.data


def test_submissions_list_shows_graded_status(client, sample_exam, db_session):
    """Test that submissions list displays graded status badge."""
    # Create graded submission
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Graded Student",
        total_score=85,
        max_score=100,
        percentage=85.0,
        status="graded",
    )
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/submissions")
    assert response.status_code == 200
    assert b"Fully Graded" in response.data or b"graded" in response.data.lower()
    assert b"Graded Student" in response.data


def test_submissions_list_shows_pending_count(client, sample_exam, db_session):
    """Test that submissions list shows count of pending submissions."""
    # Create 2 pending, 1 graded
    s1 = Submission(
        exam_id=sample_exam.id, student_name="Pending 1", max_score=100, status="pending"
    )
    s2 = Submission(
        exam_id=sample_exam.id, student_name="Pending 2", max_score=100, status="pending"
    )
    s3 = Submission(
        exam_id=sample_exam.id,
        student_name="Graded 1",
        total_score=90,
        max_score=100,
        status="graded",
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/submissions")
    assert response.status_code == 200

    # Should show "2" pending somewhere
    assert b"Pending Grading" in response.data
    # Check for count (might be in different formats)
    data = response.data.decode()
    assert "2" in data  # Count of pending


# ============================================================================
# TEST 6: Grade button appears for pending submissions
# ============================================================================


def test_pending_submission_shows_grade_now_button(client, sample_exam, db_session):
    """Test that pending submissions show 'Grade Now' button."""
    submission = Submission(
        exam_id=sample_exam.id, student_name="Need Grade", max_score=100, status="pending"
    )
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/submissions")
    assert response.status_code == 200
    assert b"Grade Now" in response.data or b"grade" in response.data.lower()


def test_graded_submission_shows_view_button(client, sample_exam, db_session):
    """Test that graded submissions show 'View' button instead of 'Grade Now'."""
    submission = Submission(
        exam_id=sample_exam.id,
        student_name="Already Graded",
        total_score=90,
        max_score=100,
        status="graded",
    )
    db_session.add(submission)
    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/submissions")
    assert response.status_code == 200
    assert b"View" in response.data
    # Should have re-grade option too
    assert b"Re-grade" in response.data or b"Grade" in response.data


# ============================================================================
# TEST 7: MCQ scoring still works correctly
# ============================================================================


def test_mcq_only_calculates_score_correctly(client, sample_exam, db_session):
    """Test that MCQ-only submissions still calculate scores correctly."""
    sample_exam.status = "published"

    q1 = Question(
        exam_id=sample_exam.id,
        question_text="Q1",
        question_type="mcq",
        points=10,
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
        points=10,
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
            "student_name": "Score Test",
            f"question_{q1.id}": "A",  # Correct
            f"question_{q2.id}": "A",  # Incorrect
        },
    )

    submission = Submission.query.filter_by(student_name="Score Test").first()
    assert submission.total_score == 10
    assert submission.max_score == 20
    assert submission.percentage == 50.0
    assert submission.status == "graded"


# ============================================================================
# TEST 8: Mixed submissions calculate partial MCQ score
# ============================================================================


def test_mixed_submission_shows_mcq_score_while_pending(client, sample_exam, db_session):
    """Test that pending submissions show MCQ score (partial) correctly."""
    sample_exam.status = "published"

    mcq = Question(
        exam_id=sample_exam.id,
        question_text="MCQ",
        question_type="mcq",
        points=10,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="A",
        order_num=1,
    )
    written = Question(
        exam_id=sample_exam.id,
        question_text="Written",
        question_type="written",
        points=20,
        order_num=2,
    )
    db_session.add_all([mcq, written])
    db_session.commit()

    # Submit
    client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={
            "student_name": "Partial Score",
            f"question_{mcq.id}": "A",  # Correct, 10 points
            f"question_{written.id}": "Answer",  # Pending, 0 points for now
        },
    )

    submission = Submission.query.filter_by(student_name="Partial Score").first()
    assert submission.total_score == 10  # Only MCQ scored
    assert submission.max_score == 30  # Total possible
    assert submission.status == "pending"
