from datetime import datetime

from .. import db


class Submission(db.Model):  # type: ignore[misc, name-defined]
    """Submission model for storing student exam submissions and grades."""

    __tablename__ = "submissions"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    student_name = db.Column(db.String(200), nullable=False)  # For now, simple name field

    # Grading info
    total_score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)

    # Status
    status = db.Column(db.String(20), default="pending")  # pending, graded
    graded_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Submission {self.id}: {self.student_name}>"

    def calculate_percentage(self):
        """Calculate percentage score."""
        if self.max_score > 0:
            self.percentage = round((self.total_score / self.max_score) * 100, 2)
        else:
            self.percentage = 0.0
        return self.percentage

    def to_dict(self):
        """Convert submission to dictionary."""
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "student_name": self.student_name,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "percentage": self.percentage,
            "status": self.status,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }


class Answer(db.Model):  # type: ignore[misc, name-defined]
    """Answer model for storing individual question answers."""

    __tablename__ = "answers"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)

    # Answer content
    answer_text = db.Column(db.Text, nullable=True)  # For written questions
    selected_option = db.Column(db.String(1), nullable=True)  # For MCQ (A, B, C, D)

    # Grading
    is_correct = db.Column(db.Boolean, default=False)  # Auto-graded for MCQ
    points_earned = db.Column(db.Integer, default=0)
    instructor_comment = db.Column(db.Text, nullable=True)  # For manual grading

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Answer {self.id}: Q{self.question_id}>"

    def to_dict(self):
        """Convert answer to dictionary."""
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "question_id": self.question_id,
            "answer_text": self.answer_text,
            "selected_option": self.selected_option,
            "is_correct": self.is_correct,
            "points_earned": self.points_earned,
            "instructor_comment": self.instructor_comment,
        }
