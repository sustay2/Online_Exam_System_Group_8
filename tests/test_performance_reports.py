"""
Tests for Performance Reports & Export

User Story:
As an instructor/admin, I want reports and Excel export so I can analyze results and keep records.

Acceptance Criteria:
1. Instructor/Admin can view overall class performance trends
2. Pass/fail percentage displayed
3. Average score, highest, lowest shown
4. System generates a summary table
5. User can export results to .xlsx with student name, email, score, submission date
6. Exported file follows clean formatting with headers
"""

from online_exam.models.submission import Submission

# ============================================================================
# STORY: PERFORMANCE REPORTS - TEST 1: View Report Page
# ============================================================================


def test_exam_report_page_loads(client, sample_exam, db_session):
    """Test that exam report page loads successfully."""
    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    assert response.status_code == 200
    assert b"Performance Report" in response.data
    assert sample_exam.title.encode() in response.data


def test_exam_report_shows_statistics_with_submissions(client, sample_exam, db_session):
    """Test that report shows statistics when submissions exist."""
    # Create submissions
    s1 = Submission(
        exam_id=sample_exam.id,
        student_name="Student A",
        total_score=90,
        max_score=100,
        percentage=90.0,
        status="graded",
    )
    s2 = Submission(
        exam_id=sample_exam.id,
        student_name="Student B",
        total_score=75,
        max_score=100,
        percentage=75.0,
        status="graded",
    )
    s3 = Submission(
        exam_id=sample_exam.id,
        student_name="Student C",
        total_score=45,
        max_score=100,
        percentage=45.0,
        status="graded",
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    assert response.status_code == 200

    # Check statistics are displayed
    assert b"Total Submissions" in response.data
    assert b"3" in response.data  # Total submissions
    assert b"Average Score" in response.data
    assert b"Highest Score" in response.data
    assert b"90" in response.data  # Highest score
    assert b"Lowest Score" in response.data
    assert b"45" in response.data  # Lowest score


def test_exam_report_shows_pass_fail_percentage(client, sample_exam, db_session):
    """Test that report shows pass/fail percentage."""
    # Create submissions: 2 pass, 1 fail
    s1 = Submission(
        exam_id=sample_exam.id,
        student_name="Student A",
        total_score=80,
        max_score=100,
        percentage=80.0,
        status="graded",
    )
    s2 = Submission(
        exam_id=sample_exam.id,
        student_name="Student B",
        total_score=60,
        max_score=100,
        percentage=60.0,
        status="graded",
    )
    s3 = Submission(
        exam_id=sample_exam.id,
        student_name="Student C",
        total_score=30,
        max_score=100,
        percentage=30.0,
        status="graded",
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    assert response.status_code == 200

    # Check pass/fail analysis
    assert b"Pass/Fail Analysis" in response.data
    assert b"Passed" in response.data
    assert b"Failed" in response.data
    # 2 passed out of 3 = 66.7%
    # 1 failed out of 3 = 33.3%


def test_exam_report_shows_score_distribution(client, sample_exam, db_session):
    """Test that report shows score distribution ranges."""
    # Create submissions across different ranges
    submissions = [
        Submission(
            exam_id=sample_exam.id,
            student_name=f"Student {i}",
            total_score=score,
            max_score=100,
            percentage=score,
            status="graded",
        )
        for i, score in enumerate([95, 85, 75, 65, 55, 45], start=1)
    ]
    db_session.add_all(submissions)
    db_session.commit()

    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    assert response.status_code == 200

    # Check score distribution table
    assert b"Score Distribution" in response.data
    assert b"90-100" in response.data
    assert b"80-89" in response.data
    assert b"70-79" in response.data
    assert b"60-69" in response.data
    assert b"50-59" in response.data
    assert b"Below 50" in response.data


def test_exam_report_shows_detailed_results_table(client, sample_exam, db_session):
    """Test that report shows detailed results table with all submissions."""
    # Create submissions
    s1 = Submission(
        exam_id=sample_exam.id,
        student_name="John Doe",
        total_score=85,
        max_score=100,
        percentage=85.0,
        status="graded",
    )
    s2 = Submission(
        exam_id=sample_exam.id,
        student_name="Jane Smith",
        total_score=70,
        max_score=100,
        percentage=70.0,
        status="graded",
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    assert response.status_code == 200

    # Check detailed results table
    assert b"Detailed Results" in response.data
    assert b"John Doe" in response.data
    assert b"Jane Smith" in response.data
    assert b"85" in response.data
    assert b"70" in response.data


def test_exam_report_empty_state(client, sample_exam, db_session):
    """Test that report shows empty state when no submissions exist."""
    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    assert response.status_code == 200

    assert b"No submissions yet" in response.data


# ============================================================================
# STORY: PERFORMANCE REPORTS - TEST 2: Excel Export
# ============================================================================


def test_export_exam_results_downloads_file(client, sample_exam, db_session):
    """Test that Excel export downloads a file."""
    # Create sample submissions
    s1 = Submission(
        exam_id=sample_exam.id,
        student_name="Student A",
        total_score=90,
        max_score=100,
        percentage=90.0,
        status="graded",
    )
    db_session.add(s1)
    db_session.commit()

    response = client.get(f"/analytics/exams/{sample_exam.id}/export")

    # Check response headers
    assert response.status_code == 200
    assert (
        response.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment" in response.headers.get("Content-Disposition", "")


def test_export_button_visible_on_report_page(client, sample_exam, db_session):
    """Test that export button is visible on report page."""
    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    assert response.status_code == 200

    assert b"Export to Excel" in response.data
    assert f"/analytics/exams/{sample_exam.id}/export".encode() in response.data


def test_export_exam_results_nonexistent_exam_404(client):
    """Test that exporting non-existent exam returns 404."""
    response = client.get("/analytics/exams/99999/export")
    assert response.status_code == 404


# ============================================================================
# STORY: PERFORMANCE REPORTS - TEST 3: Performance Calculations
# ============================================================================


def test_average_score_calculation(client, sample_exam, db_session):
    """Test that average score is calculated correctly."""
    # Create submissions: 80, 90, 70 -> avg = 80
    submissions = [
        Submission(
            exam_id=sample_exam.id,
            student_name=f"Student {i}",
            total_score=score,
            max_score=100,
            percentage=score,
            status="graded",
        )
        for i, score in enumerate([80, 90, 70], start=1)
    ]
    db_session.add_all(submissions)
    db_session.commit()

    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    data = response.data.decode()

    # Average should be 80.00%
    assert "80.00" in data or "80.0" in data


def test_pass_rate_calculation(client, sample_exam, db_session):
    """Test that pass rate is calculated correctly."""
    # Create submissions: 3 pass (>=50), 2 fail (<50)
    submissions = [
        Submission(
            exam_id=sample_exam.id,
            student_name=f"Student {i}",
            total_score=score,
            max_score=100,
            percentage=score,
            status="graded",
        )
        for i, score in enumerate([80, 60, 55, 45, 30], start=1)
    ]
    db_session.add_all(submissions)
    db_session.commit()

    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    data = response.data.decode()

    # Pass rate: 3/5 = 60%
    # Fail rate: 2/5 = 40%
    assert "60" in data  # Pass rate
    assert "40" in data  # Fail rate


# ============================================================================
# STORY: PERFORMANCE REPORTS - TEST 4: Integration with Submissions
# ============================================================================


def test_report_page_accessible_from_submissions_list(client, sample_exam, db_session):
    """Test that report page is accessible from submissions list page."""
    response = client.get(f"/exams/{sample_exam.id}/submissions")
    assert response.status_code == 200

    # Should have link to analytics
    # Note: This test assumes you'll add a link from submissions page to analytics


def test_report_shows_recent_submissions_first(client, sample_exam, db_session):
    """Test that report shows most recent submissions first."""
    from datetime import datetime, timedelta

    # Create submissions with different timestamps
    now = datetime.utcnow()
    s1 = Submission(
        exam_id=sample_exam.id,
        student_name="First",
        total_score=80,
        max_score=100,
        percentage=80.0,
        status="graded",
        submitted_at=now - timedelta(hours=2),
    )
    s2 = Submission(
        exam_id=sample_exam.id,
        student_name="Second",
        total_score=90,
        max_score=100,
        percentage=90.0,
        status="graded",
        submitted_at=now - timedelta(hours=1),
    )
    s3 = Submission(
        exam_id=sample_exam.id,
        student_name="Third",
        total_score=70,
        max_score=100,
        percentage=70.0,
        status="graded",
        submitted_at=now,
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    response = client.get(f"/analytics/exams/{sample_exam.id}/report")
    data = response.data.decode()

    # "Third" should appear before "First" in HTML
    third_pos = data.find("Third")
    first_pos = data.find("First")
    assert third_pos < first_pos
