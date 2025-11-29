from datetime import datetime

from .. import db


class Exam(db.Model):  # type: ignore[misc, name-defined]
    __tablename__ = "exams"
    __table_args__ = {'extend_existing': True}

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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
