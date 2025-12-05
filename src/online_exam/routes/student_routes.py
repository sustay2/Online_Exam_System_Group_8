# src/online_exam/routes/student_routes.py
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from ..models.exam import Exam
from ..models.attempt import ExamAttempt
from .. import db

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/take/<int:exam_id>", methods=["GET"])
@login_required
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    # Security checks
    if exam.status != "published":
        flash("This exam is not available.", "danger")
        return redirect(url_for("exam.list_exams"))

    # TODO: Add time window check (start_time / end_time) later

    # Create attempt if not exists
    attempt = ExamAttempt.query.filter_by(exam_id=exam.id, student_id=current_user.id).first()

    if not attempt:
        attempt = ExamAttempt(exam_id=exam.id, student_id=current_user.id)
        db.session.add(attempt)
        db.session.commit()

    return render_template(
        "exams/take_exam.html",
        exam=exam,
        attempt=attempt,
    )
