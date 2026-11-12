from app import db
from app.models.user import User
from app.models.complaint import Complaint
from app.services.erp_service import ERPService


def test_erp_summary_kpis_calculation(app, student_buyer, student_seller, sample_product):
    """Test dynamic computation of ERP dashboard KPIs."""
    with app.app_context():
        kpis = ERPService.get_summary_kpis()
        assert kpis["total_students"] == 2
        assert kpis["total_sellers"] == 1
        assert kpis["total_products"] == 1
        assert kpis["active_products"] == 1
        assert kpis["low_stock_count"] == 0  # stock is 3, threshold is 1


def test_user_management_toggle_status(client, admin_user, student_buyer, app):
    """Test admin toggling active status of student accounts."""
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})

    # Deactivate student
    client.post(f"/admin/users/toggle-status/{student_buyer.id}", follow_redirects=True)
    with app.app_context():
        u = db.session.get(User, student_buyer.id)
        assert u.is_active is False

    # Deactivated student cannot log in
    client.get("/auth/logout")
    login_resp = client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"}, follow_redirects=True)
    assert b"Your account has been deactivated" in login_resp.data

    # Reactivate student
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})
    client.post(f"/admin/users/toggle-status/{student_buyer.id}", follow_redirects=True)
    with app.app_context():
        u = db.session.get(User, student_buyer.id)
        assert u.is_active is True


def test_complaint_submission_and_admin_resolution(client, student_buyer, admin_user, app):
    """Test complaint filing by student and admin resolution flow."""
    # 1. Student lodges complaint
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})
    submit_resp = client.post("/student/complaints", data={
        "subject": "Missing course CD from textbook",
        "description": "Seller did not include the reference software disc.",
    }, follow_redirects=True)
    assert submit_resp.status_code == 200
    assert b"lodged successfully" in submit_resp.data

    with app.app_context():
        comp = Complaint.query.filter_by(student_id=student_buyer.id).first()
        assert comp is not None
        assert comp.status == "Pending"
        comp_id = comp.id

    # 2. Admin logs in and resolves complaint
    client.get("/auth/logout")
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})

    resolve_resp = client.post("/admin/complaints", data={
        "complaint_id": comp_id,
        "status": "Resolved",
        "admin_notes": "Contacted seller; digital download link sent to student via campus email.",
    }, follow_redirects=True)

    assert resolve_resp.status_code == 200
    assert b"updated to &#39;Resolved&#39;" in resolve_resp.data

    with app.app_context():
        comp_after = db.session.get(Complaint, comp_id)
        assert comp_after.status == "Resolved"
        assert "digital download link" in comp_after.admin_notes


def test_api_chart_data_endpoint(client, admin_user):
    """Test JSON API for Chart.js dashboard integration."""
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})
    resp = client.get("/admin/api/chart-data")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "monthly_trends" in data
    assert "category_distribution" in data
    assert "inventory_health" in data
    assert "labels" in data["monthly_trends"]
