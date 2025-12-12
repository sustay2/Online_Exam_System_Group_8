from typing import Any


def send_otp_email(user: Any, otp_code: str, expiry_minutes: int = 5) -> None:
    """Stub for sending OTP emails."""
    print(
        "Sending OTP email to"
        f" {getattr(user, 'email', '<unknown>')} with code {otp_code}."
        f" Expires in {expiry_minutes} minutes."
    )


def send_password_reset_email(user: Any, token_url: str) -> None:
    """Stub for sending password reset emails."""
    print(f"Sending password reset email to {getattr(user, 'email', '<unknown>')} at {token_url}")


def send_otp_sms(user: Any, otp_code: str) -> None:
    """Stub for sending OTP via SMS (no-op placeholder)."""
    print(f"[SMS STUB] Would send OTP {otp_code} to {getattr(user, 'phone', '<unknown>')}")
