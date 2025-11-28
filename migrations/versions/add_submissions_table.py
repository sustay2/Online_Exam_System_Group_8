"""add submissions and answers tables

Revision ID: add_submissions_table
Revises: add_questions_table
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_submissions_table"
down_revision = "add_questions_table"
branch_labels = None
depends_on = None


def upgrade():
    # Create submissions table
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("student_name", sa.String(length=200), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.Column("percentage", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("graded_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["exam_id"],
            ["exams.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("submissions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_submissions_exam_id"), ["exam_id"], unique=False)

    # Create answers table
    op.create_table(
        "answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("selected_option", sa.String(length=1), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("points_earned", sa.Integer(), nullable=True),
        sa.Column("instructor_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("answers", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_answers_submission_id"), ["submission_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_answers_question_id"), ["question_id"], unique=False)


def downgrade():
    with op.batch_alter_table("answers", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_answers_question_id"))
        batch_op.drop_index(batch_op.f("ix_answers_submission_id"))

    op.drop_table("answers")

    with op.batch_alter_table("submissions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_submissions_exam_id"))

    op.drop_table("submissions")