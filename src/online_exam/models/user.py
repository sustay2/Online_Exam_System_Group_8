from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from .. import db


class User(db.Model):  # type: ignore[misc, name-defined]
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    two_factor_enabled = db.Column(db.Boolean, nullable=False, default=False)
    otp_code = db.Column(db.String(255), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)

    tokens = db.relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def otp_is_valid(self, submitted_code: str) -> bool:
        if not self.otp_code or not self.otp_expires_at:
            return False

        if datetime.utcnow() > self.otp_expires_at:
            return False

        return check_password_hash(self.otp_code, submitted_code)
