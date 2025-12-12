import secrets
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash


OTP_EXPIRY_MINUTES = 5


def generate_otp_code(length: int = 6) -> str:
    """Generate a numeric OTP of the given length."""
    floor = 10 ** (length - 1)
    ceiling = (10**length) - 1
    return str(secrets.randbelow(ceiling - floor + 1) + floor)


def hash_otp(code: str) -> str:
    return generate_password_hash(code)


def verify_otp(hashed: str, submitted_code: str) -> bool:
    return check_password_hash(hashed, submitted_code)


def otp_expiry_time() -> datetime:
    return datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
