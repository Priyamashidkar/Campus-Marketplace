from app import db
from app.models.user import User


def test_student_registration_success(client, app):
    """Test standard student registration with unique credentials."""
    response = client.post("/auth/register", data={
        "full_name": "Test Student",
        "student_id": "TEST2026",
        "email": "test@campus.edu",
        "campus_block": "Hostel H-1",
        "phone": "+91 9999999999",
        "password": "Password123",
        "confirm_password": "Password123",
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="test@campus.edu").first()
        assert user is not None
        assert user.student_id == "TEST2026"
        assert user.check_password("Password123") is True
        assert user.is_admin is False
        assert user.cart is not None


def test_duplicate_registration_prevention(client, student_buyer):
    """Ensure duplicate email or duplicate student ID registration is blocked."""
    # Attempt duplicate email
    resp_email = client.post("/auth/register", data={
        "full_name": "Another Student",
        "student_id": "DIFF1234",
        "email": student_buyer.email,
        "password": "Password123",
        "confirm_password": "Password123",
    }, follow_redirects=True)
    assert b"An account with this email address already exists" in resp_email.data

    # Attempt duplicate student ID
    resp_id = client.post("/auth/register", data={
        "full_name": "Another Student",
        "student_id": student_buyer.student_id,
        "email": "unique@campus.edu",
        "password": "Password123",
        "confirm_password": "Password123",
    }, follow_redirects=True)
    assert b"An account with this Student ID already exists" in resp_id.data


def test_password_hashing_security(student_buyer):
    """Verify passwords are never stored plain-text and hashing works."""
    assert student_buyer.password_hash != "Student@123"
    assert student_buyer.password_hash.startswith("scrypt:") or student_buyer.password_hash.startswith("pbkdf2:")
    assert student_buyer.check_password("Student@123") is True
    assert student_buyer.check_password("WrongPassword") is False


def test_login_and_logout(client, student_buyer):
    """Verify login and session persistence, followed by logout."""
    # Correct login
    login_resp = client.post("/auth/login", data={
        "email": student_buyer.email,
        "password": "Student@123",
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Welcome back, Priya Buyer" in login_resp.data

    # Logout
    logout_resp = client.get("/auth/logout", follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"You have been safely logged out" in logout_resp.data


def test_role_based_page_restrictions(client, student_buyer, admin_user):
    """Verify non-admin users cannot access ERP admin routes."""
    # Unauthenticated attempt to access ERP dashboard
    resp_unauth = client.get("/admin/dashboard", follow_redirects=True)
    assert b"Please log in with administrator credentials" in resp_unauth.data

    # Student logged in attempting to access ERP dashboard
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})
    resp_student_admin = client.get("/admin/dashboard", follow_redirects=True)
    assert b"Access denied. Administrator privileges required" in resp_student_admin.data

    # Admin login succeeds in accessing ERP dashboard
    client.get("/auth/logout")
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})
    resp_admin = client.get("/admin/dashboard", follow_redirects=True)
    assert b"ERP Control Center" in resp_admin.data
