# src/online_exam/routes/exam_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from online_exam import db
from online_exam.models.exam import Exam
from datetime import datetime

exam_bp = Blueprint("exam", __name__, url_prefix="/exams")

@exam_bp.route("/schedule/<int:exam_id>", methods=["GET", "POST"])
def schedule_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":
        start = request.form.get("start_time")
        end = request.form.get("end_time")

        if not start or not end:
            flash("Start and end time are required.", "danger")
            return redirect(url_for("exam.schedule_exam", exam_id=exam_id))

        exam.start_time = datetime.fromisoformat(start)
        exam.end_time = datetime.fromisoformat(end)

        db.session.commit()

        flash("Exam scheduled successfully!", "success")
        
        # OPTION A: Redirect back to schedule page
        return redirect(url_for("exam.schedule_exam", exam_id=exam.id))

    return render_template("schedule_exam.html", exam=exam)
