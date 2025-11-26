from flask import Blueprint, render_template, request, redirect, url_for, flash
from .. import db
from ..models.exam import Exam

exam_bp = Blueprint("exam", __name__, url_prefix="/exams")

@exam_bp.route("/create", methods=["GET"])
def create_exam_form():
    return render_template("exams/create_exam.html")

@exam_bp.route("/create", methods=["POST"])
def create_exam():
    title = request.form.get("title")
    description = request.form.get("description")
    instructions = request.form.get("instructions")

    if not title:
        flash("Title is required.", "danger")
        return redirect(url_for("exam.create_exam_form"))

    exam = Exam(
        title=title,
        description=description,
        instructions=instructions,
        status="draft"
    )

    db.session.add(exam)
    db.session.commit()

    flash("Draft exam created successfully!", "success")

    return redirect(url_for("exam.view_exam", exam_id=exam.id))

@exam_bp.route("/<int:exam_id>")
def view_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    return render_template("exams/view_exam.html", exam=exam)