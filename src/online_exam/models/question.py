from datetime import datetime

from .. import db


class Question(db.Model):  # type: ignore[misc, name-defined]
    """Question model supporting both MCQ and written question types."""

    __tablename__ = "questions"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)

    # Question content
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'mcq' or 'written'
    points = db.Column(db.Integer, nullable=False, default=10)

    # MCQ-specific fields (only used when question_type='mcq')
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_answer = db.Column(db.String(1))  # 'A', 'B', 'C', or 'D'

    # Ordering
    order_num = db.Column(db.Integer, default=1)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Question {self.id}: {self.question_type}>"

    def is_mcq(self):
        """Check if this is an MCQ question."""
        return self.question_type == "mcq"

    def is_written(self):
        """Check if this is a written question."""
        return self.question_type == "written"

    def validate_mcq(self):
        """Validate that MCQ has all required fields."""
        if not self.is_mcq():
            return True

        # Check if all options are provided
        if not all([self.option_a, self.option_b, self.option_c, self.option_d]):
            return False

        # Check if correct answer is valid
        if self.correct_answer not in ["A", "B", "C", "D"]:
            return False

        return True

    def to_dict(self):
        """Convert question to dictionary."""
        data = {
            "id": self.id,
            "exam_id": self.exam_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "points": self.points,
            "order_num": self.order_num,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if self.is_mcq():
            data.update(
                {
                    "option_a": self.option_a,
                    "option_b": self.option_b,
                    "option_c": self.option_c,
                    "option_d": self.option_d,
                    "correct_answer": self.correct_answer,
                }
            )

        return data
