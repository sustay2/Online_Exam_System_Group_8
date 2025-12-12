from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import db
from ..models.exam import Exam
from ..models.question import Question
from ..models.submission import Answer, Submission

grading_bp = Blueprint("grading", __name__, url_prefix="/exams")


@grading_bp.route("/<int:exam_id>/submit", methods=["GET", "POST"])
def submit_exam(exam_id):
    """Submit exam answers (for testing/demo purposes)."""
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()

    if request.method == "POST":
        student_name = request.form.get("student_name", "Test Student")

        # Create submission
        submission = Submission(exam_id=exam_id, student_name=student_name, status="pending")
        db.session.add(submission)
        db.session.flush()  # Get submission ID

        total_score = 0
        max_score = 0

        # Process answers
        for question in questions:
            max_score += question.points

            if question.is_mcq():
                selected_option = request.form.get(f"question_{question.id}")
                if selected_option:
                    selected_option = selected_option.upper()
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
                answer_text = request.form.get(f"question_{question.id}", "")
                answer = Answer(
                    submission_id=submission.id,
                    question_id=question.id,
                    answer_text=answer_text,
                    is_correct=False,
                    points_earned=0,
                )
                db.session.add(answer)

        # Update submission
        submission.total_score = total_score
        submission.max_score = max_score
        submission.calculate_percentage()
        submission.status = "graded"
        submission.graded_at = datetime.utcnow()

        db.session.commit()

        flash(
            f"Exam submitted successfully! Score: {total_score}/{max_score} ({submission.percentage}%)",
            "success",
        )
        return redirect(url_for("grading.view_results", submission_id=submission.id))

    return render_template("grading/submit_exam.html", exam=exam, questions=questions)


@grading_bp.route("/submissions/<int:submission_id>")
def view_results(submission_id):
    """View submission results."""
    submission = Submission.query.get_or_404(submission_id)
    exam = Exam.query.get_or_404(submission.exam_id)

    answers = (
        db.session.query(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .filter(Answer.submission_id == submission_id)
        .order_by(Question.order_num)
        .all()
    )

    return render_template(
        "grading/view_results.html", submission=submission, exam=exam, answers=answers
    )


@grading_bp.route("/<int:exam_id>/submissions")
def list_submissions(exam_id):
    """List all submissions for an exam."""
    exam = Exam.query.get_or_404(exam_id)
    submissions = (
        Submission.query.filter_by(exam_id=exam_id).order_by(Submission.submitted_at.desc()).all()
    )

    return render_template("grading/list_submissions.html", exam=exam, submissions=submissions)


@grading_bp.route("/submissions/<int:submission_id>/grade", methods=["GET", "POST"])
def manual_grade(submission_id):
    """Manually grade written questions and update submission status."""
    submission = Submission.query.get_or_404(submission_id)
    exam = Exam.query.get_or_404(submission.exam_id)

    answers = (
        db.session.query(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .filter(Answer.submission_id == submission_id)
        .order_by(Question.order_num)
        .all()
    )

    if request.method == "POST":
        total_score = 0
        max_score = 0

        for answer, question in answers:
            max_score += question.points

            if question.is_mcq():
                # MCQ already graded
                total_score += answer.points_earned
            else:
                # Grade written question
                points_str = request.form.get(f"points_{answer.id}", "0")
                try:
                    points = int(points_str)
                except ValueError:
                    points = 0

                points = max(0, min(points, question.points))
                comment = request.form.get(f"comment_{answer.id}", "").strip()

                answer.points_earned = points
                answer.instructor_comment = comment
                answer.is_correct = points == question.points

                total_score += points

        # Update submission
        submission.total_score = total_score
        submission.max_score = max_score
        submission.calculate_percentage()

        # CHANGE STATUS TO GRADED (Instructor has finished grading)
        submission.status = "graded"
        submission.graded_at = datetime.utcnow()

        db.session.commit()

        flash(
            f"✅ Grading completed! Final Score: {total_score}/{max_score} ({submission.percentage}%)",
            "success",
        )
        return redirect(url_for("grading.view_results", submission_id=submission_id))

    return render_template(
        "grading/manual_grade.html", submission=submission, exam=exam, answers=answers
    )


@grading_bp.route("/<int:exam_id>/publish_grades", methods=["POST"])
def publish_grades(exam_id: int):
    """Publish grades for all graded submissions of an exam."""
    exam = Exam.query.get_or_404(exam_id)

    graded_submissions = Submission.query.filter_by(exam_id=exam.id, status="graded").all()

    if not graded_submissions:
        flash("No graded submissions to publish.", "warning")
        return redirect(url_for("exam.view_exam", exam_id=exam.id))

    for submission in graded_submissions:
        submission.status = "published"

    db.session.commit()
    flash("Grades published successfully", "success")

    return redirect(url_for("exam.view_exam", exam_id=exam.id))


