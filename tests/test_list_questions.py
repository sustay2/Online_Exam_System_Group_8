from online_exam.models.exam import Exam
from online_exam.models.question import Question


def test_list_questions_page_loads(client, sample_exam):
    """Test that list questions page loads successfully."""
    response = client.get(f"/exams/{sample_exam.id}/questions")
    assert response.status_code == 200
    assert sample_exam.title.encode() in response.data


def test_list_questions_shows_all_questions(client, sample_exam, db_session):
    """Test that all questions are displayed in the list."""
    # Create MCQ question
    mcq = Question(
        exam_id=sample_exam.id,
        question_text="What is 2 + 2?",
        question_type="mcq",
        points=5,
        option_a="3",
        option_b="4",
        option_c="5",
        option_d="6",
        correct_answer="B",
        order_num=1,
    )

    # Create written question
    written = Question(
        exam_id=sample_exam.id, question_text="Explain the water cycle.", question_type="written", points=10, order_num=2
    )

    db_session.add_all([mcq, written])
    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/questions")
    assert response.status_code == 200
    assert b"What is 2 + 2?" in response.data
    assert b"Explain the water cycle." in response.data


def test_list_questions_shows_statistics(client, sample_exam, db_session):
    """Test that question statistics are displayed correctly."""
    # Create 3 MCQ questions
    for i in range(3):
        mcq = Question(
            exam_id=sample_exam.id,
            question_text=f"MCQ Question {i+1}",
            question_type="mcq",
            points=10,
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
            order_num=i + 1,
        )
        db_session.add(mcq)

    # Create 2 written questions
    for i in range(2):
        written = Question(
            exam_id=sample_exam.id,
            question_text=f"Written Question {i+1}",
            question_type="written",
            points=15,
            order_num=i + 4,
        )
        db_session.add(written)

    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/questions")
    assert response.status_code == 200

    # Check statistics
    # Total: 5, MCQ: 3, Written: 2, Points: (3*10) + (2*15) = 60
    data = response.data.decode()
    assert "5" in data  # Total questions
    assert "3" in data  # MCQ count
    assert "2" in data  # Written count
    assert "60" in data  # Total points


def test_list_questions_empty_state(client, sample_exam):
    """Test that empty state is shown when no questions exist."""
    response = client.get(f"/exams/{sample_exam.id}/questions")
    assert response.status_code == 200
    assert b"No questions added yet" in response.data
    assert b"Add First Question" in response.data


def test_list_questions_preserves_order(client, sample_exam, db_session):
    """Test that questions are displayed in order."""
    # Create questions out of order
    q3 = Question(
        exam_id=sample_exam.id, question_text="Question 3", question_type="written", points=10, order_num=3
    )
    q1 = Question(
        exam_id=sample_exam.id, question_text="Question 1", question_type="written", points=10, order_num=1
    )
    q2 = Question(
        exam_id=sample_exam.id, question_text="Question 2", question_type="written", points=10, order_num=2
    )

    db_session.add_all([q3, q1, q2])
    db_session.commit()

    response = client.get(f"/exams/{sample_exam.id}/questions")
    data = response.data.decode()

    # Check that questions appear in correct order
    pos1 = data.find("Question 1")
    pos2 = data.find("Question 2")
    pos3 = data.find("Question 3")

    assert pos1 < pos2 < pos3


def test_list_questions_shows_edit_delete_buttons(client, sample_question):
    """Test that edit and delete buttons are shown for draft exams."""
    response = client.get(f"/exams/{sample_question.exam_id}/questions")
    assert response.status_code == 200
    assert b"Edit" in response.data
    assert b"Delete" in response.data


def test_list_questions_hides_buttons_for_published(client, db_session, sample_instructor):
    """Test that edit/delete buttons are hidden for published exams."""
    # Create a published exam
    exam = Exam(
    title="Published Exam",
    description="Test Description",
    instructions="Test instructions",
    status="published",
)
    db_session.add(exam)
    db_session.commit()

    # Create a question
    question = Question(
        exam_id=exam.id, question_text="Test question", question_type="written", points=10, order_num=1
    )
    db_session.add(question)
    db_session.commit()

    response = client.get(f"/exams/{exam.id}/questions")
    assert response.status_code == 200
    assert b"Locked" in response.data
    assert b'href="/exams/' not in response.data or b"/edit" not in response.data  # No edit link