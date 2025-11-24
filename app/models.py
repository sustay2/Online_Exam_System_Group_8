from app import db
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')
    def __repr__(self):
        return f'<Exam {self.title} - {self.status}>'
