from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import db
from ..models.exam import Exam

exam_bp = Blueprint("exam", __name__, url_prefix="/exams")


@exam_bp.route("/create", methods=["GET"])
def create_exam_form():
    return render_template("exams/create_exam.html")


@exam_bp.route("", methods=["GET"])
def list_exams():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "all")
    sort = request.args.get("sort", "newest")
    page = request.args.get("page", 1, type=int)

    query = Exam.query

    if search:
        query = query.filter(Exam.title.ilike(f"%{search}%"))

    if status == "draft":
        query = query.filter_by(status="draft")
    elif status == "published":
        query = query.filter_by(status="published")

    if sort == "oldest":
        query = query.order_by(Exam.created_at.asc())
    else:
        query = query.order_by(Exam.created_at.desc())

    pagination = query.paginate(page=page, per_page=10, error_out=False)

    return render_template(
        "exams/list_exams.html",
        exams=pagination.items,
        pagination=pagination,
        search=search,
        status=status,
        sort=sort,
        total_exams=Exam.query.count(),
        total_drafts=Exam.query.filter_by(status="draft").count(),
        total_published=Exam.query.filter_by(status="published").count(),
    )


@exam_bp.route("/create", methods=["POST"])
def create_exam():
    title = request.form.get("title")
    description = request.form.get("description")
    instructions = request.form.get("instructions")

    if not title:
        flash("Title is required.", "danger")
        return redirect(url_for("exam.create_exam_form"))

    exam = Exam(title=title, description=description, instructions=instructions, status="draft")

    db.session.add(exam)
    db.session.commit()

    flash("Draft exam created successfully!", "success")
    return redirect(url_for("exam.view_exam", exam_id=exam.id))


@exam_bp.route("/<int:exam_id>/edit", methods=["GET", "POST"])
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    # BLOCK EDITING AFTER PUBLISH
    if exam.status == "published":
        flash("Cannot edit a published exam.", "danger")
        return redirect(url_for("exam.view_exam", exam_id=exam.id))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        instructions = request.form.get("instructions")

        if not title:
            flash("Title is required.", "danger")
            return render_template("exams/edit_exam.html", exam=exam)

        exam.title = title
        exam.description = description
        exam.instructions = instructions
        exam.updated_at = datetime.utcnow()

        db.session.commit()

        flash("Exam updated successfully!", "success")
        return redirect(url_for("exam.view_exam", exam_id=exam.id))

    return render_template("exams/edit_exam.html", exam=exam)


@exam_bp.route("/<int:exam_id>")
def view_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    return render_template("exams/view_exam.html", exam=exam)


@exam_bp.route("/<int:exam_id>/publish", methods=["POST"])
def publish_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if exam.status == "published":
        flash("This exam is already published.", "info")
    else:
        exam.status = "published"
        db.session.commit()
        flash("Exam published successfully! Students can now see it.", "success")

    return redirect(url_for("exam.view_exam", exam_id=exam.id))
