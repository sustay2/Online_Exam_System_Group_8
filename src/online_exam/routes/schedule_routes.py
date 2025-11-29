from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from online_exam import db
from online_exam.models.exam import Exam

schedule_bp = Blueprint("schedule", __name__, url_prefix="/exams")


@schedule_bp.route("/schedule/<int:exam_id>", methods=["GET", "POST"])
def schedule_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":
        start = request.form.get("start_time")
        end = request.form.get("end_time")

        if not start or not end:
            flash("Start and end time are required.", "error")
            return render_template("schedule_exam.html", exam=exam)

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        if end_dt <= start_dt:
            flash("End time must be after start time.", "error")
            return render_template("schedule_exam.html", exam=exam)

        exam.start_time = start_dt
        exam.end_time = end_dt
        exam.status = "scheduled"

        db.session.commit()
        flash("Exam scheduled successfully!", "success")
        return redirect(url_for("exam.view_exam", exam_id=exam.id))

    return render_template("schedule_exam.html", exam=exam)
