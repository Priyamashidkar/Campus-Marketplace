import re
from flask import current_app


def is_valid_student_id(student_id: str) -> bool:
    """Validate student ID format: alphanumeric, 4 to 20 characters."""
    if not student_id or not isinstance(student_id, str):
        return False
    return bool(re.match(r"^[A-Za-z0-9\-_]{4,20}$", student_id.strip()))


def is_valid_campus_email(email: str) -> tuple[bool, str]:
    """
    Validate email address format and optional university campus domain.
    Returns (is_valid, error_message).
    """
    if not email or not isinstance(email, str):
        return False, "Email address is required."

    email = email.strip().lower()
    email_regex = r"^[\w\.-]+@([\w\.-]+)\.([a-zA-Z]{2,})$"
    match = re.match(email_regex, email)
    if not match:
        return False, "Please enter a valid email address format."

    domain = email.split("@")[-1]

    # Check configurable campus email domain enforcement
    if current_app.config.get("ENFORCE_CAMPUS_EMAIL", False):
        allowed_domains = current_app.config.get("CAMPUS_EMAIL_DOMAINS", [])
        if not any(domain == d or domain.endswith("." + d) for d in allowed_domains):
            allowed_list_str = ", ".join(f"@{d}" for d in allowed_domains)
            return False, f"Please use your official university email ({allowed_list_str})."

    return True, ""
