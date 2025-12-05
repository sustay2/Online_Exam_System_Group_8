from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from online_exam import db
from online_exam.models.exam import Exam
from online_exam.models.question import Question
from online_exam.models.submission import Answer, Submission

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/exams/<int:exam_id>/take", methods=["GET"])
def take_exam(exam_id):
    """Display exam for student to take."""
    exam = Exam.query.get_or_404(exam_id)

    # Only allow published exams
    if exam.status != "published":
        flash("This exam is not available yet.", "warning")
        return redirect(url_for("exam.list_exams"))

    # Get all questions ordered by order_num
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()

    # Calculate total points
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
    submission.status = "graded"
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

    # Get all answers with their questions
    answers = (
        db.session.query(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .filter(Answer.submission_id == submission_id)
        .order_by(Question.order_num)
        .all()
    )

    return render_template(
        "student/view_results.html", submission=submission, exam=exam, answers=answers
    )
