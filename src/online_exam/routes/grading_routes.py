from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from online_exam import db
from online_exam.models.exam import Exam
from online_exam.models.question import Question
from online_exam.models.submission import Answer, Submission

grading_bp = Blueprint("grading", __name__, url_prefix="/exams")


@grading_bp.route("/<int:exam_id>/submit", methods=["GET", "POST"])
def submit_exam(exam_id):
    """Submit exam answers (for testing/demo purposes)."""
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()

    if request.method == "POST":
        student_name = request.form.get("student_name", "Test Student")

        # Create submission
        submission = Submission(
            exam_id=exam_id,
            student_name=student_name,
            status="pending"
        )
        db.session.add(submission)
        db.session.flush()  # Get submission ID

        total_score = 0
        max_score = 0

        # Process answers
        for question in questions:
            max_score += question.points

            if question.is_mcq():
                # Get selected option
                selected_option = request.form.get(f"question_{question.id}")
                
                if selected_option:
                    selected_option = selected_option.upper()
                    is_correct = (selected_option == question.correct_answer)
                    points_earned = question.points if is_correct else 0
                    total_score += points_earned

                    answer = Answer(
                        submission_id=submission.id,
                        question_id=question.id,
                        selected_option=selected_option,
                        is_correct=is_correct,
                        points_earned=points_earned
                    )
                    db.session.add(answer)
            else:
                # Written question - save answer text, no auto-grading
                answer_text = request.form.get(f"question_{question.id}", "")
                answer = Answer(
                    submission_id=submission.id,
                    question_id=question.id,
                    answer_text=answer_text,
                    is_correct=False,
                    points_earned=0  # Will be manually graded
                )
                db.session.add(answer)

        # Update submission with scores
        submission.total_score = total_score
        submission.max_score = max_score
        submission.calculate_percentage()
        submission.status = "graded"
        submission.graded_at = datetime.utcnow()

        db.session.commit()

        flash(f"Exam submitted successfully! Score: {total_score}/{max_score} ({submission.percentage}%)", "success")
        return redirect(url_for("grading.view_results", submission_id=submission.id))

    return render_template("grading/submit_exam.html", exam=exam, questions=questions)


@grading_bp.route("/submissions/<int:submission_id>")
def view_results(submission_id):
    """View submission results."""
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
        "grading/view_results.html",
        submission=submission,
        exam=exam,
        answers=answers
    )


@grading_bp.route("/<int:exam_id>/submissions")
def list_submissions(exam_id):
    """List all submissions for an exam."""
    exam = Exam.query.get_or_404(exam_id)
    submissions = Submission.query.filter_by(exam_id=exam_id).order_by(Submission.submitted_at.desc()).all()

    return render_template(
        "grading/list_submissions.html",
        exam=exam,
        submissions=submissions
    )

@grading_bp.route("/submissions/<int:submission_id>/grade", methods=["GET", "POST"])
def manual_grade(submission_id):
    """Manually grade written questions."""
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

    if request.method == "POST":
        total_score = 0
        max_score = 0

        # Process grading for each question
        for answer, question in answers:
            max_score += question.points

            if question.is_mcq():
                # MCQ already graded, just add to total
                total_score += answer.points_earned
            else:
                # Manual grading for written questions
                points_str = request.form.get(f"points_{answer.id}", "0")
                try:
                    points = int(points_str)
                except ValueError:
                    points = 0
                
                # Validate points don't exceed max
                if points > question.points:
                    points = question.points
                if points < 0:
                    points = 0
                    
                comment = request.form.get(f"comment_{answer.id}", "").strip()
                
                # Update answer
                answer.points_earned = points
                answer.instructor_comment = comment
                answer.is_correct = (points == question.points)
                
                total_score += points

        # Update submission
        submission.total_score = total_score
        submission.max_score = max_score
        submission.calculate_percentage()
        submission.status = "graded"
        submission.graded_at = datetime.utcnow()

        db.session.commit()

        flash(f"Grading saved successfully! Final Score: {total_score}/{max_score} ({submission.percentage}%)", "success")
        return redirect(url_for("grading.view_results", submission_id=submission_id))

    return render_template(
        "grading/manual_grade.html",
        submission=submission,
        exam=exam,
        answers=answers
    )