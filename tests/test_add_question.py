from online_exam.models.exam import Exam
from online_exam.models.question import Question


def test_add_question_page_loads(client, sample_exam):
    """Test that add question page loads successfully."""
    response = client.get(f"/exams/{sample_exam.id}/questions/add")
    assert response.status_code == 200
    assert b"Add New Question" in response.data


def test_add_mcq_question_success(client, sample_exam, db_session):
    """Test successfully adding an MCQ question."""
    response = client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={
            "question_text": "What is 2 + 2?",
            "question_type": "mcq",
            "points": 5,
            "option_a": "3",
            "option_b": "4",
            "option_c": "5",
            "option_d": "6",
            "correct_answer": "B",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Question added successfully!" in response.data

    # Verify question was created
    question = Question.query.filter_by(exam_id=sample_exam.id).first()
    assert question is not None
    assert question.question_text == "What is 2 + 2?"
    assert question.question_type == "mcq"
    assert question.points == 5
    assert question.option_b == "4"
    assert question.correct_answer == "B"
    assert question.order_num == 1


def test_add_written_question_success(client, sample_exam, db_session):
    """Test successfully adding a written question."""
    response = client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={"question_text": "Explain the water cycle.", "question_type": "written", "points": 10},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Question added successfully!" in response.data

    # Verify question was created
    question = Question.query.filter_by(exam_id=sample_exam.id).first()
    assert question is not None
    assert question.question_text == "Explain the water cycle."
    assert question.question_type == "written"
    assert question.points == 10


def test_add_question_missing_text(client, sample_exam, db_session):
    """Test adding question with missing text shows error."""
    response = client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={"question_text": "", "question_type": "written", "points": 10},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Question text is required" in response.data

    # Verify no question was created
    question = Question.query.filter_by(exam_id=sample_exam.id).first()
    assert question is None


def test_add_mcq_missing_options(client, sample_exam, db_session):
    """Test adding MCQ without all options shows error."""
    response = client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={
            "question_text": "What is 2 + 2?",
            "question_type": "mcq",
            "points": 5,
            "option_a": "3",
            "option_b": "4",
            # Missing option_c and option_d
            "correct_answer": "B",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"All four options are required" in response.data

    # Verify no question was created
    question = Question.query.filter_by(exam_id=sample_exam.id).first()
    assert question is None


def test_add_mcq_invalid_correct_answer(client, sample_exam, db_session):
    """Test adding MCQ with invalid correct answer shows error."""
    response = client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={
            "question_text": "What is 2 + 2?",
            "question_type": "mcq",
            "points": 5,
            "option_a": "3",
            "option_b": "4",
            "option_c": "5",
            "option_d": "6",
            "correct_answer": "E",  # Invalid
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Correct answer must be A, B, C, or D" in response.data


def test_add_question_invalid_points(client, sample_exam, db_session):
    """Test adding question with invalid points shows error."""
    response = client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={"question_text": "Test question", "question_type": "written", "points": 0},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Points must be greater than 0" in response.data


def test_add_multiple_questions_order(client, sample_exam, db_session):
    """Test that multiple questions get correct order numbers."""
    # Add first question
    client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={"question_text": "Question 1", "question_type": "written", "points": 10},
    )

    # Add second question
    client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={"question_text": "Question 2", "question_type": "written", "points": 10},
    )

    # Add third question
    client.post(
        f"/exams/{sample_exam.id}/questions/add",
        data={"question_text": "Question 3", "question_type": "written", "points": 10},
    )

    # Verify order numbers
    questions = Question.query.filter_by(exam_id=sample_exam.id).order_by(Question.order_num).all()
    assert len(questions) == 3
    assert questions[0].order_num == 1
    assert questions[1].order_num == 2
    assert questions[2].order_num == 3


def test_cannot_add_question_to_published_exam(client, db_session, sample_instructor):
    """Test that questions cannot be added to published exams."""
    # Create a published exam
    exam = Exam(
    title="Published Exam",
    description="Test Description",
    instructions="Test instructions",
    status="published",
    )
    db_session.add(exam)
    db_session.commit()

    response = client.post(
        f"/exams/{exam.id}/questions/add",
        data={"question_text": "Test question", "question_type": "written", "points": 10},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Cannot add questions to a published exam" in response.data

    # Verify no question was created
    question = Question.query.filter_by(exam_id=exam.id).first()
    assert question is None