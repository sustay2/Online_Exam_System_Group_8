from datetime import datetime

from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .. import db
from ..models.exam import Exam
from ..models.question import Question
from ..models.submission import Answer, Submission

student_bp = Blueprint("student", __name__, url_prefix="/student")


# ============================================================================
# STUDENT DASHBOARD
# ============================================================================


@student_bp.route("/dashboard")
def dashboard():
    """Student dashboard showing available exams and past results."""
    # Get user from session
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access student dashboard.", "warning")
        return redirect(url_for("auth.login"))

    # Get student's email from session
    from ..models.user import User

    user = User.query.get(user_id)

    # Get all published exams
    available_exams = (
        Exam.query.filter_by(status="published").order_by(Exam.created_at.desc()).all()
    )

    # Get student's past submissions
    my_submissions = Submission.query.order_by(Submission.submitted_at.desc()).limit(10).all()

    # Calculate statistics
    total_exams_taken = len(my_submissions)
    if my_submissions:
        avg_score = sum(s.percentage for s in my_submissions) / len(my_submissions)
        highest_score = max(s.percentage for s in my_submissions)
        lowest_score = min(s.percentage for s in my_submissions)
    else:
        avg_score = 0
        highest_score = 0
        lowest_score = 0

    return render_template(
        "student/dashboard.html",
        available_exams=available_exams,
        my_submissions=my_submissions,
        total_exams_taken=total_exams_taken,
        avg_score=avg_score,
        highest_score=highest_score,
        lowest_score=lowest_score,
        student_name=user.name if user else "Student",
    )


# ============================================================================
# TAKE EXAM
# ============================================================================


@student_bp.route("/exams/<int:exam_id>/take", methods=["GET"])
def take_exam(exam_id):
    """Display exam for student to take."""
    exam = Exam.query.get_or_404(exam_id)

    if exam.status != "published":
        flash("This exam is not available yet.", "warning")
        return redirect(url_for("student.dashboard"))

    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()
    total_points = sum(q.points for q in questions)

    return render_template(
        "student/take_exam.html",
        exam=exam,
        questions=questions,
        total_questions=len(questions),
        total_points=total_points,
    )


@student_bp.route("/exams/<int:exam_id>/submit", methods=["POST"])
def submit_exam(exam_id):
    """Process student exam submission."""
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()

    # Get student name
    student_name = request.form.get("student_name", "").strip()
    if not student_name:
        flash("Student name is required.", "danger")
        return redirect(url_for("student.take_exam", exam_id=exam_id))

    # Create submission
    submission = Submission(exam_id=exam_id, student_name=student_name, status="pending")
    db.session.add(submission)
    db.session.flush()  # Get submission ID

    total_score = 0
    max_score = 0

    # Process each question
    for question in questions:
        max_score += question.points

        if question.is_mcq():
            # Process MCQ answer
            selected_option = request.form.get(f"question_{question.id}", "").strip().upper()

            if selected_option:
                is_correct = selected_option == question.correct_answer
                points_earned = question.points if is_correct else 0
                total_score += points_earned

                answer = Answer(
                    submission_id=submission.id,
                    question_id=question.id,
                    selected_option=selected_option,
                    is_correct=is_correct,
                    points_earned=points_earned,
                )
                db.session.add(answer)
        else:
            # Process written answer
            answer_text = request.form.get(f"question_{question.id}", "").strip()

            answer = Answer(
                submission_id=submission.id,
                question_id=question.id,
                answer_text=answer_text,
                is_correct=False,
                points_earned=0,  # Needs manual grading
            )
            db.session.add(answer)

    # Update submission with final scores
    submission.total_score = total_score
    submission.max_score = max_score
    submission.calculate_percentage()
    submission.status = "graded"  # Auto-graded submissions
    submission.graded_at = datetime.utcnow()

    db.session.commit()

    flash(
        f"✅ Exam submitted successfully! Your score: {total_score}/{max_score} ({submission.percentage}%)",
        "success",
    )

    return redirect(url_for("student.view_results", submission_id=submission.id))


@student_bp.route("/submissions/<int:submission_id>/results", methods=["GET"])
def view_results(submission_id):
    """Display exam results for student."""
    submission = Submission.query.get_or_404(submission_id)
    exam = Exam.query.get_or_404(submission.exam_id)

    # If results are not graded -> redirect to dashboard with flash
    if submission.status != "graded":
        flash("Results not available yet", "warning")
        return redirect(url_for("student.dashboard"))

    # Now show results page safely
    answers = (
        db.session.query(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .filter(Answer.submission_id == submission_id)
        .order_by(Question.order_num)
        .all()
    )

    return render_template(
        "student/view_results.html",
        submission=submission,
        exam=exam,
        answers=answers,
    )


@student_bp.route("/submissions/<int:submission_id>/download", methods=["GET"])
def download_results(submission_id):
    """Download detailed grade breakdown as CSV."""
    submission = Submission.query.get_or_404(submission_id)

    if submission.status != "graded":
        flash("Results not available yet.", "warning")
        return redirect(url_for("student.dashboard"))

    # Get answers
    answers = (
        db.session.query(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .filter(Answer.submission_id == submission_id)
        .order_by(Question.order_num)
        .all()
    )

    # CSV data
    csv_data = [
        [
            "Question No",
            "Type",
            "Question",
            "Your Answer",
            "Correct Answer",
            "Points",
            "Instructor Comments",
        ]
    ]

    for answer, question in answers:
        qtype = "MCQ" if question.is_mcq() else "Written"
        your_answer = answer.selected_option if question.is_mcq() else (answer.answer_text or "")
        correct_answer = question.correct_answer if question.is_mcq() else ""
        points = answer.points_earned
        comment = answer.instructor_comment or ""
        csv_data.append(
            [
                question.order_num,
                qtype,
                question.question_text,
                your_answer,
                correct_answer,
                points,
                comment,
            ]
        )

    # Create response
    output = make_response("\n".join([",".join(map(str, row)) for row in csv_data]))
    output.headers["Content-Disposition"] = f"attachment; filename=grades_{submission.id}.csv"
    output.headers["Content-Type"] = "text/csv"
    return output
