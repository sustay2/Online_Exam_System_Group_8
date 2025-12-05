from typing import Any


def send_password_reset_email(user: Any, token_url: str) -> None:
    """Stub for sending password reset emails."""
    print(f"Sending password reset email to {getattr(user, 'email', '<unknown>')} at {token_url}")
