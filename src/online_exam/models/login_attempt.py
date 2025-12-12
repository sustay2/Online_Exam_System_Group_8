from datetime import datetime

from .. import db


class LoginAttempt(db.Model):  # type: ignore[misc, name-defined]
    __tablename__ = "login_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    success = db.Column(db.Boolean, nullable=False)

    @classmethod
    def recent_failed(cls, limit: int = 20):
        """Return the most recent failed attempts for admin review."""

        return cls.query.filter_by(success=False).order_by(cls.timestamp.desc()).limit(limit).all()

    @classmethod
    def failed_counts_by_ip(cls, limit: int = 20):
        """Return failed attempt counts grouped by IP for quick triage."""

        return (
            db.session.query(cls.ip_address, db.func.count(cls.id).label("attempt_count"))
            .filter_by(success=False)
            .group_by(cls.ip_address)
            .order_by(db.func.count(cls.id).desc())
            .limit(limit)
            .all()
        )
