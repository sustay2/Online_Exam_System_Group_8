"""
Tests for Story 7: Student Question Flagging (Mark for Review)

User Story:
As a student, I want to flag questions while taking the exam so I can return to them before submitting.

Acceptance Criteria:
1. "Mark for Review" toggle on each question
2. Review panel displays flagged questions
3. Flags cleared automatically when submitted
4. Does not affect grading
"""

from online_exam.models.question import Question
from online_exam.models.submission import Submission


# ============================================================================
# STORY 7 - TEST 1: Flag UI Elements Present
# ============================================================================


def test_take_exam_has_flag_buttons(client, sample_exam, db_session):
    """Test that each question has a 'Mark for Review' button."""
    sample_exam.status = "published"

    # Create questions
    q1 = Question(
        exam_id=sample_exam.id,
        question_text="Question 1",
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
        question_text="Question 2",
        question_type="written",
        points=20,
        order_num=2,
    )
    db_session.add_all([q1, q2])
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for flag buttons
    assert b"Mark for Review" in response.data
    assert b"flag-btn" in response.data

    # Check there are 2 flag buttons (one per question)
    assert response.data.count(b'class="btn btn-sm btn-outline-warning flag-btn"') == 2


def test_take_exam_has_flagged_counter(client, sample_exam, db_session):
    """Test that page has a counter for flagged questions."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for flagged counter
    assert b"Flagged" in response.data
    assert b"flaggedCount" in response.data
    assert b'<h2 class="mb-0 text-warning" id="flaggedCount">0</h2>' in response.data


def test_take_exam_has_review_panel(client, sample_exam, db_session):
    """Test that page has a review panel for flagged questions."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for review panel
    assert b"Flagged Questions for Review" in response.data
    assert b"reviewPanel" in response.data
    assert b"flaggedList" in response.data


def test_take_exam_has_flag_warning_on_submit(client, sample_exam, db_session):
    """Test that submit section shows warning about flagged questions."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for flagged warning
    assert b"flaggedWarning" in response.data
    assert b"You have" in response.data
    assert b"flagged question" in response.data


# ============================================================================
# STORY 7 - TEST 2: JavaScript Functionality
# ============================================================================


def test_take_exam_has_flagging_javascript(client, sample_exam, db_session):
    """Test that page includes JavaScript for flagging functionality."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for key JavaScript functions
    assert b"toggleFlag" in response.data
    assert b"updateFlaggedPanel" in response.data
    assert b"loadFlags" in response.data
    assert b"saveFlags" in response.data


def test_flagging_uses_localstorage(client, sample_exam, db_session):
    """Test that flagging uses localStorage for persistence."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for localStorage usage
    assert b"localStorage.getItem" in response.data
    assert b"localStorage.setItem" in response.data
    assert b"flagStorageKey" in response.data
    assert b"exam_' + examId + '_flagged" in response.data


def test_flags_cleared_on_submission(client, sample_exam, db_session):
    """Test that flags are cleared from localStorage on form submission."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check that submission clears flags
    assert b"localStorage.removeItem(flagStorageKey)" in response.data
    assert b"formSubmitted = true" in response.data


# ============================================================================
# STORY 7 - TEST 3: Flagging Does Not Affect Grading
# ============================================================================


def test_submission_without_flags_works_normally(client, sample_exam, db_session):
    """Test that submission works normally without any flagged questions."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="Test Question",
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

    # Submit exam (no flags data sent, since it's client-side only)
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "Test Student", f"question_{question.id}": "A"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Exam submitted successfully!" in response.data

    # Verify submission was created and graded correctly
    submission = Submission.query.filter_by(student_name="Test Student").first()
    assert submission is not None
    assert submission.total_score == 10
    assert submission.percentage == 100.0


def test_flagged_questions_do_not_appear_in_submission(client, sample_exam, db_session):
    """Test that flagging is purely client-side and doesn't affect backend."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="Flagged Question",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    # Submit exam with answer
    # Note: Flags are client-side only, no flag data is sent to server
    response = client.post(
        f"/student/exams/{sample_exam.id}/submit",
        data={"student_name": "Flag Test", f"question_{question.id}": "My answer"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify submission - flags should not be stored in database
    submission = Submission.query.filter_by(student_name="Flag Test").first()
    assert submission is not None
    # No flag-related fields in database models


# ============================================================================
# STORY 7 - TEST 4: UI/UX Features
# ============================================================================


def test_question_cards_have_data_attributes(client, sample_exam, db_session):
    """Test that question cards have data attributes for JavaScript."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="Test",
        question_type="written",
        points=10,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for data attributes
    assert b"data-question-id" in response.data
    assert b"data-question-num" in response.data
    assert b'id="question-' in response.data


def test_review_panel_is_collapsible(client, sample_exam, db_session):
    """Test that review panel uses Bootstrap collapse."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for Bootstrap collapse attributes
    assert b'data-bs-toggle="collapse"' in response.data
    assert b'data-bs-target="#reviewPanel"' in response.data
    assert b'class="collapse"' in response.data


def test_flag_indicator_badge_present(client, sample_exam, db_session):
    """Test that questions have a flag indicator badge (hidden by default)."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="Test",
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

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check for flag indicator
    assert b'class="badge bg-danger ms-2 flag-indicator"' in response.data
    assert b'style="display: none;"' in response.data
    assert b"bi-flag-fill" in response.data
    assert b"Flagged" in response.data


# ============================================================================
# STORY 7 - TEST 5: Multiple Questions
# ============================================================================


def test_multiple_questions_all_have_flag_buttons(client, sample_exam, db_session):
    """Test that each question has its own independent flag button."""
    sample_exam.status = "published"

    # Create 5 questions
    for i in range(1, 6):
        q = Question(
            exam_id=sample_exam.id,
            question_text=f"Question {i}",
            question_type="written",
            points=10,
            order_num=i,
        )
        db_session.add(q)
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Should have 5 flag buttons
    assert response.data.count(b"Mark for Review") >= 5
    assert response.data.count(b'class="btn btn-sm btn-outline-warning flag-btn"') == 5


# ============================================================================
# STORY 7 - TEST 6: Integration with Existing Features
# ============================================================================


def test_flagging_works_with_mcq_questions(client, sample_exam, db_session):
    """Test that flagging works with MCQ questions."""
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

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # MCQ should have flag button
    assert b"Multiple Choice" in response.data
    assert b"Mark for Review" in response.data


def test_flagging_works_with_written_questions(client, sample_exam, db_session):
    """Test that flagging works with written questions."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="Written Question",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Written should have flag button
    assert b"Written Answer" in response.data
    assert b"Mark for Review" in response.data


def test_flagging_coexists_with_autosave(client, sample_exam, db_session):
    """Test that flagging doesn't interfere with auto-save functionality."""
    sample_exam.status = "published"

    question = Question(
        exam_id=sample_exam.id,
        question_text="Written Question",
        question_type="written",
        points=20,
        order_num=1,
    )
    db_session.add(question)
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Both flagging and auto-save should be present
    assert b"toggleFlag" in response.data
    assert b"auto-save-indicator" in response.data
    assert b"localStorage" in response.data


# ============================================================================
# STORY 7 - TEST 7: Edge Cases
# ============================================================================


def test_exam_with_no_questions_no_errors(client, sample_exam, db_session):
    """Test that page loads correctly even with no questions."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Should still have flagging infrastructure
    assert b"flaggedCount" in response.data
    assert b"reviewPanel" in response.data


def test_flagging_persists_storage_key_format(client, sample_exam, db_session):
    """Test that localStorage key format is correct and exam-specific."""
    sample_exam.status = "published"
    db_session.commit()

    response = client.get(f"/student/exams/{sample_exam.id}/take")
    assert response.status_code == 200

    # Check localStorage key format includes exam ID
    assert b"'exam_' + examId + '_flagged'" in response.data
    assert b"var examId" in response.data
