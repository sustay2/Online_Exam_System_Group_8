from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
class CreateExamForm(FlaskForm):
    title = StringField('Exam Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    instructions = TextAreaField('Instructions for Students')
    submit = SubmitField('Create Draft Exam')
