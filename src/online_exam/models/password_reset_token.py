from datetime import datetime, timedelta

from .. import db


class PasswordResetToken(db.Model):  # type: ignore[misc, name-defined]
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", back_populates="tokens")

    @classmethod
    def create_for_user(cls, user_id: int, token: str, expires_in_minutes: int = 30):
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        return cls(user_id=user_id, token=token, expires_at=expires_at)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
