from datetime import datetime, timedelta
from online_exam.models.exam import Exam


def seed_exams(db):

    now = datetime.utcnow()

    e1 = Exam(
        title="Draft Exam 1",
        description="Desc 1",
        instructions="Instr 1",
        status="draft",
        created_at=now - timedelta(minutes=2),
        updated_at=now - timedelta(minutes=2),
    )

    e2 = Exam(
        title="Published Exam",
        description="Desc 2",
        instructions="Instr 2",
        status="published",
        created_at=now - timedelta(minutes=1),
        updated_at=now - timedelta(minutes=1),
    )

    e3 = Exam(
        title="Draft Exam 2",
        description="Desc 3",
        instructions="Instr 3",
        status="draft",
        created_at=now,
        updated_at=now,
    )

    db.session.add_all([e1, e2, e3])
    db.session.commit()


# 1. List exams page loads
def test_list_exams_page_loads(client, app):
    with app.app_context():
        from online_exam import db

        seed_exams(db)

    response = client.get("/exams")
    assert response.status_code == 200
    assert b"Exam Dashboard" in response.data


# 2. Shows all exams
def test_list_exams_shows_all_items(client, app):
    with app.app_context():
        from online_exam import db

        seed_exams(db)

    response = client.get("/exams")
    assert response.data.count(b"Draft Exam") >= 2
    assert b"Published Exam" in response.data


# 3. Search filtering
def test_list_exams_search(client, app):
    with app.app_context():
        from online_exam import db

        seed_exams(db)

    response = client.get("/exams?search=Published")
    assert response.status_code == 200
    assert b"Published Exam" in response.data
    table_html = response.data.split(b"<tbody>")[1].split(b"</tbody>")[0]
    assert b"Draft Exam" not in table_html


# 4. Status filter
def test_list_exams_filter_status(client, app):
    with app.app_context():
        from online_exam import db

        seed_exams(db)

    response = client.get("/exams?status=draft")
    assert b"Draft Exam" in response.data
    table_html = response.data.split(b"<tbody>")[1].split(b"</tbody>")[0]
    assert b"Published Exam" not in table_html


# 5. Sorting by oldest (created_at ascending)
def test_list_exams_sort_oldest(client, app):
    with app.app_context():
        from online_exam import db

        seed_exams(db)

    response = client.get("/exams?sort=oldest")
    html = response.data.decode()

    table_html = html.split("<tbody>")[1].split("</tbody>")[0]

    first = table_html.find("Draft Exam 1")
    second = table_html.find("Published Exam")
    third = table_html.find("Draft Exam 2")

    assert first < second < third


# 6. Sorting by newest (created_at descending)
def test_list_exams_sort_newest(client, app):
    with app.app_context():
        from online_exam import db

        seed_exams(db)

    response = client.get("/exams?sort=newest")
    html = response.data.decode()

    table_html = html.split("<tbody>")[1].split("</tbody>")[0]

    first = table_html.find("Draft Exam 2")
    second = table_html.find("Published Exam")
    third = table_html.find("Draft Exam 1")

    assert first < second < third
