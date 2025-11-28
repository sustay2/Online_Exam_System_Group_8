from datetime import datetime
from online_exam import db

class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)

    status = db.Column(db.String(20), default="draft")  # draft, scheduled, published

    # NEW FIELDS
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
