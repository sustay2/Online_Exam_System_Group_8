from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import db
from ..models.exam import Exam
from ..models.question import Question

question_bp = Blueprint("question", __name__, url_prefix="/exams")


@question_bp.route("/<int:exam_id>/questions")
def list_questions(exam_id):
    """List all questions for an exam."""
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_num).all()

    # Calculate statistics
    total_questions = len(questions)
    mcq_count = sum(1 for q in questions if q.is_mcq())
    written_count = sum(1 for q in questions if q.is_written())
    total_points = sum(q.points for q in questions)

    return render_template(
        "questions/list_questions.html",
        exam=exam,
        questions=questions,
        total_questions=total_questions,
        mcq_count=mcq_count,
        written_count=written_count,
        total_points=total_points,
    )


@question_bp.route("/<int:exam_id>/questions/add", methods=["GET", "POST"])
def add_question(exam_id):
    """Add a new question to an exam."""
    exam = Exam.query.get_or_404(exam_id)

    # Prevent adding questions to published exams
    if exam.status == "published":
        flash("Cannot add questions to a published exam.", "error")
        return redirect(url_for("question.list_questions", exam_id=exam_id))

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        question_type = request.form.get("question_type", "mcq")
        points = request.form.get("points", 10, type=int)

        # Validation
        if not question_text:
            flash("Question text is required.", "error")
            return redirect(url_for("question.add_question", exam_id=exam_id))

        if points <= 0:
            flash("Points must be greater than 0.", "error")
            return redirect(url_for("question.add_question", exam_id=exam_id))

        if question_type not in ["mcq", "written"]:
            flash("Invalid question type.", "error")
            return redirect(url_for("question.add_question", exam_id=exam_id))

        # Get the next order number
        max_order = (
            db.session.query(db.func.max(Question.order_num)).filter_by(exam_id=exam_id).scalar()
        )
        order_num = (max_order or 0) + 1

        # Create question
        question = Question(
            exam_id=exam_id,
            question_text=question_text,
            question_type=question_type,
            points=points,
            order_num=order_num,
        )

        # Handle MCQ-specific fields
        if question_type == "mcq":
            option_a = request.form.get("option_a", "").strip()
            option_b = request.form.get("option_b", "").strip()
            option_c = request.form.get("option_c", "").strip()
            option_d = request.form.get("option_d", "").strip()
            correct_answer = request.form.get("correct_answer", "").upper()

            # Validate MCQ fields
            if not all([option_a, option_b, option_c, option_d]):
                flash("All four options are required for MCQ questions.", "error")
                return redirect(url_for("question.add_question", exam_id=exam_id))

            if correct_answer not in ["A", "B", "C", "D"]:
                flash("Correct answer must be A, B, C, or D.", "error")
                return redirect(url_for("question.add_question", exam_id=exam_id))

            question.option_a = option_a
            question.option_b = option_b
            question.option_c = option_c
            question.option_d = option_d
            question.correct_answer = correct_answer

        # Save to database
        db.session.add(question)
        db.session.commit()

        flash("Question added successfully!", "success")
        return redirect(url_for("question.list_questions", exam_id=exam_id))

    return render_template("questions/add_question.html", exam=exam)


@question_bp.route("/<int:exam_id>/questions/<int:question_id>/edit", methods=["GET", "POST"])
def edit_question(exam_id, question_id):
    """Edit an existing question."""
    exam = Exam.query.get_or_404(exam_id)
    question = Question.query.get_or_404(question_id)

    # Verify question belongs to exam
    if question.exam_id != exam_id:
        flash("Question not found in this exam.", "error")
        return redirect(url_for("question.list_questions", exam_id=exam_id))

    # Prevent editing questions in published exams
    if exam.status == "published":
        flash("Cannot edit questions in a published exam.", "error")
        return redirect(url_for("question.list_questions", exam_id=exam_id))

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        points = request.form.get("points", 10, type=int)

        # Validation
        if not question_text:
            flash("Question text is required.", "error")
            return redirect(
                url_for("question.edit_question", exam_id=exam_id, question_id=question_id)
            )

        if points <= 0:
            flash("Points must be greater than 0.", "error")
            return redirect(
                url_for("question.edit_question", exam_id=exam_id, question_id=question_id)
            )

        # Update question
        question.question_text = question_text
        question.points = points

        # Handle MCQ-specific fields
        if question.is_mcq():
            option_a = request.form.get("option_a", "").strip()
            option_b = request.form.get("option_b", "").strip()
            option_c = request.form.get("option_c", "").strip()
            option_d = request.form.get("option_d", "").strip()
            correct_answer = request.form.get("correct_answer", "").upper()

            # Validate MCQ fields
            if not all([option_a, option_b, option_c, option_d]):
                flash("All four options are required for MCQ questions.", "error")
                return redirect(
                    url_for("question.edit_question", exam_id=exam_id, question_id=question_id)
                )

            if correct_answer not in ["A", "B", "C", "D"]:
                flash("Correct answer must be A, B, C, or D.", "error")
                return redirect(
                    url_for("question.edit_question", exam_id=exam_id, question_id=question_id)
                )

            question.option_a = option_a
            question.option_b = option_b
            question.option_c = option_c
            question.option_d = option_d
            question.correct_answer = correct_answer

        # Save to database
        db.session.commit()

        flash("Question updated successfully!", "success")
        return redirect(url_for("question.list_questions", exam_id=exam_id))

    return render_template("questions/edit_question.html", exam=exam, question=question)


@question_bp.route("/<int:exam_id>/questions/<int:question_id>/delete", methods=["POST"])
def delete_question(exam_id, question_id):
    """Delete a question."""
    exam = Exam.query.get_or_404(exam_id)
    question = Question.query.get_or_404(question_id)

    # Verify question belongs to exam
    if question.exam_id != exam_id:
        flash("Question not found in this exam.", "error")
        return redirect(url_for("question.list_questions", exam_id=exam_id))

    # Prevent deleting questions from published exams
    if exam.status == "published":
        flash("Cannot delete questions from a published exam.", "error")
        return redirect(url_for("question.list_questions", exam_id=exam_id))

    # Delete question
    db.session.delete(question)
    db.session.commit()

    flash("Question deleted successfully!", "success")
    return redirect(url_for("question.list_questions", exam_id=exam_id))
