import pytest

from online_exam import create_app, db
from online_exam.config import Config
from online_exam.models.exam import Exam
from online_exam.models.question import Question
from online_exam.models.user import User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Provide database session for tests."""
    with app.app_context():
        yield db.session


@pytest.fixture
def sample_instructor(app):
    """Create a sample instructor user."""
    with app.app_context():
        instructor = User(
            username="instructor1",
            email="instructor@example.com",
            role="instructor",
            password_hash="",
        )
        instructor.set_password("Password123!")
        db.session.add(instructor)
        db.session.commit()
        yield instructor


@pytest.fixture
def sample_student(app):
    """Create a sample student user."""
    with app.app_context():
        student = User(
            username="student1",
            email="student@example.com",
            role="student",
            password_hash="",
        )
        student.set_password("Password123!")
        db.session.add(student)
        db.session.commit()
        yield student


@pytest.fixture
def sample_exam(app, sample_instructor):
    """Create a sample exam."""
    with app.app_context():
        exam = Exam(
            title="Test Exam",
            description="Test Description",
            instructions="Test instructions",
            status="draft",
        )
        db.session.add(exam)
        db.session.commit()
        yield exam


@pytest.fixture
def sample_question(app, sample_exam):
    """Create a sample question."""
    with app.app_context():
        question = Question(
            exam_id=sample_exam.id,
            question_text="What is 2 + 2?",
            question_type="written",
            points=10,
            order_num=1,
        )
        db.session.add(question)
        db.session.commit()
        yield question


@pytest.fixture
def sample_mcq_question(app, sample_exam):
    """Create a sample MCQ question."""
    with app.app_context():
        question = Question(
            exam_id=sample_exam.id,
            question_text="What is 2 + 2?",
            question_type="mcq",
            points=10,
            option_a="3",
            option_b="4",
            option_c="5",
            option_d="6",
            correct_answer="B",
            order_num=1,
        )
        db.session.add(question)
        db.session.commit()
        yield question
