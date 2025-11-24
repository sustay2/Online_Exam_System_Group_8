from flask import Blueprint, render_template, flash, redirect, url_for
from app import db
from app.models import Exam
from app.forms import CreateExamForm
bp = Blueprint('main', __name__)
@bp.route('/')
def index():
    return '<h1>Online Exam System - Group 8</h1><p><a href="/create_exam">Create New Exam (Story 1.1)</a></p>'
@bp.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    form = CreateExamForm()
    if form.validate_on_submit():
        exam = Exam(title=form.title.data, description=form.description.data, instructions=form.instructions.data)
        db.session.add(exam)
        db.session.commit()
        flash(f'Exam "{exam.title}" created as draft!', 'success')
        return redirect(url_for('main.edit_exam', exam_id=exam.id))
    return render_template('create_exam.html', form=form)
@bp.route('/exam/<int:exam_id>/edit', methods=['GET', 'POST'])
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.status != 'draft':
        flash('Cannot edit published exam!', 'danger')
        return redirect(url_for('main.index'))
    form = CreateExamForm(obj=exam)
    if form.validate_on_submit():
        exam.title = form.title.data
        exam.description = form.description.data
        exam.instructions = form.instructions.data
        db.session.commit()
        flash('Draft updated!', 'success')
    return render_template('edit_exam.html', form=form, exam=exam)
