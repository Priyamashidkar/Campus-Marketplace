from app import db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order


def test_restore_admin_login_credentials_box(client, admin_user):
    """Verify default administrator credentials box is restored on admin login page."""
    resp = client.get("/auth/admin-login")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # The visible default credentials box must be restored directly below submit button
    assert "Default Administrator Credentials:" in html
    assert "admin@campus.edu" in html
    assert "Admin@123" in html
    assert "bi-key-fill text-warning" in html
    assert "border-warning-subtle" in html

    # Existing form elements must remain intact
    assert "Administrator Email" in html
    assert "Administrator Password" in html
    assert "Access ERP Control Center" in html
    assert "name=\"email\"" in html
    assert "name=\"password\"" in html

    # Admin authentication must continue to function properly
    login_resp = client.post("/auth/admin-login", data={
        "email": admin_user.email,
        "password": "Admin@123",
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert "ERP Control Center & Analytics" in login_resp.data.decode("utf-8")


def test_restore_dashboard_dispute_tickets_section(client, admin_user, sample_product, app):
    """Verify Recent Dispute Tickets section is restored on ERP dashboard."""
    # Seed a couple of complaints so entries are visible
    with app.app_context():
        from app.models.complaint import Complaint
        from datetime import datetime
        comp1 = Complaint(
            ticket_number="TKT-20261110-B183C9",
            student_id=admin_user.id,
            subject="Pickup timing coordination request",
            description="Could not locate seller at library.",
            status="Under Review",
            created_at=datetime.utcnow(),
        )
        comp2 = Complaint(
            ticket_number="TKT-20261105-E381A2",
            student_id=admin_user.id,
            subject="Inquiry regarding battery cover on Casio calculator",
            description="Item has cosmetic scratches.",
            status="Resolved",
            created_at=datetime.utcnow(),
        )
        db.session.add(comp1)
        db.session.add(comp2)
        db.session.commit()

    client.post("/auth/admin-login", data={
        "email": admin_user.email,
        "password": "Admin@123",
    })

    dash_resp = client.get("/admin/dashboard")
    assert dash_resp.status_code == 200
    html = dash_resp.data.decode("utf-8")

    # Recent Dispute Tickets section, its heading, and Review All button must be restored
    assert "Recent Dispute Tickets" in html
    assert "Review All" in html
    assert "bi-shield-exclamation text-warning" in html
    assert "TKT-20261110-B183C9" in html
    assert "Pickup timing coordination request" in html
    assert "Under Review" in html
    assert "bg-info text-dark" in html
    assert "Resolved" in html
    assert "bg-success" in html

    # Other ERP dashboard sections must remain intact
    assert "ERP Control Center & Analytics" in html
    assert "Monthly Marketplace Trends" in html
    assert "Category Distribution" in html
    assert "Recent Marketplace Orders" in html
    assert "Low-Stock Inventory Alerts" in html


def test_dispute_submission_persistence_and_dashboard_integration(client, student_buyer, admin_user, app):
    """Test full dispute lifecycle: student submit -> DB persist -> admin dashboard -> status update."""
    from app.models.complaint import Complaint

    # 1. Student lodges complaint
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})
    submit_resp = client.post("/student/complaints", data={
        "subject": "Missing textbook solution manual",
        "description": "Seller advertised physical companion booklet which was omitted.",
    }, follow_redirects=True)
    assert submit_resp.status_code == 200
    assert b"lodged successfully" in submit_resp.data

    with app.app_context():
        comp = Complaint.query.filter_by(subject="Missing textbook solution manual").first()
        assert comp is not None
        assert comp.ticket_number.startswith("TKT-")
        assert comp.status == "Pending"
        assert comp.description == "Seller advertised physical companion booklet which was omitted."
        ticket_num = comp.ticket_number
        comp_id = comp.id

    # 2. Check that it appears in admin dashboard
    client.get("/auth/logout")
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})
    dash_resp = client.get("/admin/dashboard")
    assert dash_resp.status_code == 200
    dash_html = dash_resp.data.decode("utf-8")
    assert ticket_num in dash_html
    assert "Missing textbook solution manual" in dash_html

    # 3. Test Review All complaints route
    comp_resp = client.get("/admin/complaints")
    assert comp_resp.status_code == 200
    comp_html = comp_resp.data.decode("utf-8")
    assert ticket_num in comp_html
    assert "Complaint & Dispute Ticket Center" in comp_html

    # 4. Test individual ticket detail page
    detail_resp = client.get(f"/admin/complaints/{comp_id}")
    assert detail_resp.status_code == 200
    detail_html = detail_resp.data.decode("utf-8")
    assert ticket_num in detail_html
    assert "Missing textbook solution manual" in detail_html
    assert student_buyer.full_name in detail_html

    # 5. Admin updates status to 'Under Review'
    update_resp = client.post(f"/admin/complaints/{comp_id}", data={
        "status": "Under Review",
        "admin_notes": "Contacting seller for confirmation.",
    }, follow_redirects=True)
    assert update_resp.status_code == 200

    with app.app_context():
        comp_check = db.session.get(Complaint, comp_id)
        assert comp_check.status == "Under Review"

    # 6. Admin updates status to 'Resolved'
    resolve_resp = client.post(f"/admin/complaints/{comp_id}", data={
        "status": "Resolved",
        "admin_notes": "Seller provided PDF manual to buyer via email.",
    }, follow_redirects=True)
    assert resolve_resp.status_code == 200

    with app.app_context():
        comp_resolved = db.session.get(Complaint, comp_id)
        assert comp_resolved.status == "Resolved"
        assert "Seller provided PDF manual" in comp_resolved.admin_notes

    # 7. Check dashboard reflects Resolved status immediately
    dash_after = client.get("/admin/dashboard")
    dash_after_html = dash_after.data.decode("utf-8")
    assert ticket_num in dash_after_html
    assert "bg-success" in dash_after_html

    # 8. Check student can view resolved dispute in their history
    client.get("/auth/logout")
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})
    stu_resp = client.get("/student/complaints")
    assert stu_resp.status_code == 200
    stu_html = stu_resp.data.decode("utf-8")
    assert ticket_num in stu_html
    assert "Seller provided PDF manual" in stu_html


def test_unauthorized_student_cannot_access_admin_disputes(client, student_buyer, app):
    """Verify unauthorized student cannot access administrator ticket-management routes."""
    from app.models.complaint import Complaint
    from datetime import datetime

    with app.app_context():
        comp = Complaint(
            ticket_number="TKT-SECURITY-TEST",
            student_id=student_buyer.id,
            subject="Security check",
            description="Testing access restriction.",
            status="Pending",
            created_at=datetime.utcnow(),
        )
        db.session.add(comp)
        db.session.commit()
        comp_id = comp.id

    # Unauthenticated access
    resp = client.get("/admin/complaints", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/admin-login" in resp.headers["Location"]

    detail_resp = client.get(f"/admin/complaints/{comp_id}", follow_redirects=False)
    assert detail_resp.status_code == 302
    assert "/auth/admin-login" in detail_resp.headers["Location"]

    # Student login (non-admin)
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})

    # Student attempting to access admin complaints
    student_access = client.get("/admin/complaints", follow_redirects=True)
    assert b"Administrator privileges required" in student_access.data

    student_detail_access = client.get(f"/admin/complaints/{comp_id}", follow_redirects=True)
    assert b"Administrator privileges required" in student_detail_access.data

    student_post = client.post(f"/admin/complaints/{comp_id}", data={
        "status": "Resolved",
    }, follow_redirects=True)
    assert b"Administrator privileges required" in student_post.data


def test_change3_dark_mode_applied_across_pages(client, student_buyer, admin_user, sample_product):
    """CHANGE 3: Verify dark mode is applied across pages and centralized CSS variables exist."""
    # 1. Base template has data-bs-theme="dark"
    pages_to_check = [
        "/",
        "/about",
        "/auth/login",
        "/auth/register",
        "/auth/admin-login",
        "/student/marketplace",
        f"/student/product/{sample_product.id}",
    ]

    for page in pages_to_check:
        resp = client.get(page)
        assert resp.status_code == 200, f"Failed loading {page}"
        html = resp.data.decode("utf-8")
        assert 'data-bs-theme="dark"' in html, f"data-bs-theme='dark' missing from {page}"
        assert 'custom.css' in html, f"custom.css link missing from {page}"

    # 2. Authenticated Student Pages
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})
    # Add an item to cart so /student/checkout does not redirect
    client.post(f"/student/cart/add/{sample_product.id}", data={"quantity": 1})

    student_pages = [
        "/student/cart",
        "/student/checkout",
        "/student/my-orders",
        "/student/profile",
        "/student/complaints",
        "/seller/dashboard",
        "/seller/products",
        "/seller/products/add",
        "/seller/orders",
        "/seller/sales-history",
    ]
    for page in student_pages:
        resp = client.get(page)
        assert resp.status_code == 200, f"Failed loading {page}"
        html = resp.data.decode("utf-8")
        assert 'data-bs-theme="dark"' in html, f"data-bs-theme='dark' missing from {page}"

    client.get("/auth/logout")

    # 3. Authenticated Admin Pages
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})
    admin_pages = [
        "/admin/dashboard",
        "/admin/inventory",
        "/admin/orders",
        "/admin/transactions",
        "/admin/users",
        "/admin/products",
        "/admin/categories",
        "/admin/complaints",
        "/admin/reports",
    ]
    for page in admin_pages:
        resp = client.get(page)
        assert resp.status_code == 200, f"Failed loading {page}"
        html = resp.data.decode("utf-8")
        assert 'data-bs-theme="dark"' in html, f"data-bs-theme='dark' missing from {page}"


def test_dark_mode_css_palette():
    """Verify that custom.css defines the requested color palette."""
    with open("app/static/css/custom.css", "r") as f:
        css = f.read()

    expected_colors = [
        ("#0F1117", "Main page background"),
        ("#161B22", "Secondary background"),
        ("#1C2330", "Cards and panels"),
        ("#252D3A", "Input backgrounds"),
        ("#F1F5F9", "Primary text"),
        ("#AAB4C3", "Secondary text"),
        ("#303B4B", "Borders"),
        ("#3B82F6", "Primary accent"),
        ("#14B8A6", "Secondary accent"),
        ("#22C55E", "Success"),
        ("#F59E0B", "Warning"),
        ("#EF4444", "Error"),
    ]

    for color, name in expected_colors:
        assert color in css or color.lower() in css.lower(), f"Expected color {color} ({name}) not found in custom.css"
