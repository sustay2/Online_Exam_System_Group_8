from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from src.online_exam.models.exam import Exam
from src.online_exam import db

schedule_bp = Blueprint("schedule", __name__)

@schedule_bp.route("/exams/<int:exam_id>/schedule", methods=["GET", "POST"])
def schedule_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":
        start = request.form.get("start_time")
        end = request.form.get("end_time")
        duration = request.form.get("duration")

        if not start or not end or not duration:
            flash("All scheduling fields are required.", "error")
            return render_template("schedule_exam.html", exam=exam)

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        if end_dt <= start_dt:
            flash("End time must be after start time.", "error")
            return render_template("schedule_exam.html", exam=exam)

        exam.start_time = start_dt
        exam.end_time = end_dt
        exam.duration_minutes = int(duration)
        exam.status = "scheduled"

        db.session.commit()
        flash("Exam scheduled successfully!", "success")
        return redirect(url_for("exam.view_exam", exam_id=exam.id))

    return render_template("schedule_exam.html", exam=exam)
