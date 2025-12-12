from flask import Blueprint

from ..utils.auth import login_required, role_required

rbac_bp = Blueprint("rbac", __name__, url_prefix="/rbac")


@rbac_bp.route("/admin-only")
@role_required("admin")
def admin_only():
    return "Admin area"


@rbac_bp.route("/instructor-only")
@login_required
@role_required("instructor")
def instructor_only():
    return "Instructor area"


@rbac_bp.route("/student-only")
@login_required
@role_required("student")
def student_only():
    return "Student area"
